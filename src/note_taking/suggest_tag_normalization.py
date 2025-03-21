import click
from collections import defaultdict
from src.note_taking.notes_database import NotesDatabase
from src.note_taking.git_utils import check_if_behind_remote, pull_latest_changes

class TagNormalizationSuggestion:
    """Class to represent a tag normalization suggestion."""
    def __init__(self, note_ids: list[int], note_titles: list[str], tags: dict[str, int], 
                 most_common_tag: str):
        self.note_ids = note_ids
        self.note_titles = note_titles
        self.tags = tags  # dict mapping tag_name -> count
        self.most_common_tag = most_common_tag
        
    def get_other_tags(self, keep_tag: str | None = None) -> list[str]:
        """Return list of tags other than the specified keep tag."""
        tag_to_keep = keep_tag or self.most_common_tag
        return [tag for tag in self.tags.keys() if tag != tag_to_keep]
    
    def __str__(self) -> str:
        """String representation of the suggestion."""
        notes_list = "\n      ".join([f"• {title}" for title in self.note_titles])
        tags_list = ", ".join([f"{tag} ({count})" for tag, count in self.tags.items()])
        note_ids_str = ",".join(map(str, self.note_ids))
        
        # Sort tags by usage count (descending)
        sorted_tags = sorted(self.tags.items(), key=lambda x: x[1], reverse=True)
        tag_options = "\n      ".join([f"• {tag} ({count} notes)" for tag, count in sorted_tags])
        
        # Create examples using multiple tag options
        examples = []
        for tag, _ in sorted_tags:
            other_tags = ",".join([f'"{t}"' for t in self.get_other_tags(tag)])
            examples.append(
                f"    # To keep '{tag}' and replace others:\n"
                f"    apply-tag-normalization --note-ids {note_ids_str} --keep-tag \"{tag}\" --replace-tags {other_tags}"
            )
        
        command_examples = "\n\n".join(examples)
        
        return (
            f"Found a group of similar notes with different tags:\n"
            f"    Notes ({len(self.note_ids)}):\n"
            f"      {notes_list}\n\n"
            f"    Current tag usage:\n"
            f"      {tag_options}\n\n"
            f"    Options to normalize these tags:\n\n"
            f"{command_examples}"
        )


def cluster_similar_notes(db: NotesDatabase, similarity_threshold: float = 0.85) -> list[list[dict]]:
    """
    Cluster notes based on their semantic similarity using DuckDB's vector operations
    with a single efficient query to find all similar note pairs.
    
    Args:
        db: NotesDatabase instance
        similarity_threshold: Threshold for considering notes similar (cosine similarity)
        
    Returns:
        list of clusters, where each cluster is a list of similar notes
    """
    # Calculate distance threshold (distance = 1 - similarity for cosine)
    distance_threshold = 1.0 - similarity_threshold
    
    # Get all note data with tags first
    notes_data = {}
    notes_with_tags = db.conn.execute("""
        SELECT 
            n.note_id, 
            n.title, 
            (SELECT STRING_AGG(t.name, ', ') 
             FROM note_tags nt 
             JOIN tags t ON nt.tag_id = t.tag_id 
             WHERE nt.note_id = n.note_id) AS tags
        FROM notes n
        WHERE EXISTS (
            SELECT 1 FROM note_tags nt WHERE nt.note_id = n.note_id
        )
    """).fetchall()
    
    if not notes_with_tags:
        return []
    
    # Convert to dictionary for quick lookup
    for note in notes_with_tags:
        note_id, title, tags = note
        tags_list = [tag.strip() for tag in (tags.split(',') if tags else [])]
        
        if tags_list:  # Only include notes with tags
            notes_data[note_id] = {
                'note_id': note_id,
                'title': title,
                'tags': tags_list
            }
    
    if not notes_data:
        return []
    
    # Get all similar note pairs in a single query using self-join
    # This is much more efficient than multiple queries
    click.echo("Finding all similar note pairs...")
    similar_pairs_query = """
        -- Get all pairs of notes where:
        -- 1. Both notes have tags
        -- 2. Their embeddings are similar (within threshold)
        -- 3. We only need one direction of pairs (n1.note_id < n2.note_id)
        SELECT 
            n1.note_id as note1_id,
            n2.note_id as note2_id,
            n1.embedding <=> n2.embedding as distance
        FROM 
            notes n1, 
            notes n2
        WHERE 
            -- Only compare notes with different IDs
            n1.note_id < n2.note_id AND
            
            -- Only include notes with tags
            EXISTS (SELECT 1 FROM note_tags nt1 WHERE nt1.note_id = n1.note_id) AND
            EXISTS (SELECT 1 FROM note_tags nt2 WHERE nt2.note_id = n2.note_id) AND
            
            -- Similarity threshold
            n1.embedding <=> n2.embedding <= ?
        ORDER BY 
            note1_id, distance
    """
    
    similar_pairs = db.conn.execute(similar_pairs_query, (distance_threshold,)).fetchall()
    
    if not similar_pairs:
        return []
    
    # Build an adjacency list to represent the similarity graph
    similarity_graph = {}
    for note1_id, note2_id, distance in similar_pairs:
        if note1_id not in similarity_graph:
            similarity_graph[note1_id] = []
        if note2_id not in similarity_graph:
            similarity_graph[note2_id] = []
        
        similarity_graph[note1_id].append((note2_id, distance))
        similarity_graph[note2_id].append((note1_id, distance))
    
    # Now use depth-first search to find connected components (clusters)
    clusters = []
    visited = set()
    
    click.echo("Forming clusters from similar notes...")
    for note_id in similarity_graph:
        if note_id in visited:
            continue
        
        # Start a new cluster with DFS
        cluster = []
        stack = [note_id]
        
        while stack:
            current_id = stack.pop()
            
            if current_id in visited:
                continue
                
            visited.add(current_id)
            
            if current_id in notes_data:
                cluster.append(notes_data[current_id])
            
            # Add all unvisited neighbors
            for neighbor_id, _ in similarity_graph.get(current_id, []):
                if neighbor_id not in visited:
                    stack.append(neighbor_id)
        
        # Only add clusters with at least 2 notes
        if len(cluster) >= 2:
            clusters.append(cluster)
    
    return clusters


def find_tag_normalization_suggestions(clusters: list[list[dict]]) -> list[TagNormalizationSuggestion]:
    """
    Analyze clusters to find tag normalization suggestions.
    
    Args:
        clusters: list of clusters, where each cluster is a list of similar notes
        
    Returns:
        list of TagNormalizationSuggestion objects
    """
    suggestions = []
    
    for cluster in clusters:
        # Count tag occurrences in this cluster
        tag_counts = defaultdict(int)
        for note in cluster:
            for tag in note['tags']:
                tag_counts[tag] += 1
        
        # If all notes have the same tags, skip this cluster
        if len(tag_counts) <= 1:
            continue
        
        # Find the most common tag
        most_common_tag = max(tag_counts.items(), key=lambda x: x[1])[0]
        
        # Check if there are multiple tags and at least one inconsistency
        if len(tag_counts) > 1:
            # Create a suggestion for this cluster
            suggestion = TagNormalizationSuggestion(
                note_ids=[note['note_id'] for note in cluster],
                note_titles=[note['title'] for note in cluster],
                tags=dict(tag_counts),
                most_common_tag=most_common_tag
            )
            suggestions.append(suggestion)
    
    return suggestions


@click.command(help="""
Analyze notes and suggest tag normalizations based on semantic similarity.

This command identifies clusters of semantically similar notes that have different 
tags and suggests standardizing them. It helps maintain a consistent tagging system
by finding potentially redundant or inconsistent tags.

The suggestions are displayed but not applied. Use the 'apply-tag-normalization'
command to apply selected normalizations.
""")
@click.option("--similarity-threshold", default=0.85, type=float, 
              help="Similarity threshold (0.0-1.0) for considering notes as similar")
@click.option("--min-cluster-size", default=2, type=int,
              help="Minimum number of notes in a cluster to suggest normalization")
def suggest_tag_normalization(similarity_threshold: float = 0.85, min_cluster_size: int = 2):
    """Suggest tag normalizations based on semantically similar notes."""
    # Check Git repository status first
    is_behind, message = check_if_behind_remote()
    
    if is_behind:
        click.echo("Repository is behind remote. Pulling latest changes...")
        
        success, pull_message = pull_latest_changes()
        if success:
            click.echo("✓ Successfully pulled latest changes from GitHub")
        else:
            click.echo(f"Error syncing with GitHub: {pull_message}", err=True)
            click.echo("Proceeding with analysis using local database (may not include latest notes)")
    
    # Initialize the database
    db = NotesDatabase(db_name="notes")
    
    try:
        click.echo("Analyzing notes and identifying similar content with different tags...")
        
        # Cluster similar notes
        clusters = cluster_similar_notes(db, similarity_threshold)
        
        # Filter clusters by minimum size
        clusters = [cluster for cluster in clusters if len(cluster) >= min_cluster_size]
        
        if not clusters:
            click.echo("No clusters of similar notes with different tags found.")
            return
        
        # Find tag normalization suggestions
        suggestions = find_tag_normalization_suggestions(clusters)
        
        if not suggestions:
            click.echo("No tag normalization suggestions found.")
            return
        
        # Display suggestions
        click.echo(f"\n--- Tag Normalization Suggestions ({len(suggestions)}) ---\n")
        
        for i, suggestion in enumerate(suggestions, 1):
            click.echo(f"Group #{i}:")
            click.echo(str(suggestion))
            click.echo("-" * 50)
        
        click.echo("\nReview the suggestions above and run your chosen command to apply the normalization you prefer.")
        
    except Exception as e:
        click.echo(f"Error analyzing tags: {str(e)}", err=True)
    finally:
        # Close the database connection
        db.close()


if __name__ == "__main__":
    suggest_tag_normalization()
