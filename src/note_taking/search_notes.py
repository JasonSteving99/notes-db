import click
from typing import Optional
from src.note_taking.notes_database import NotesDatabase
from src.note_taking.embed_content import get_embedding
from src.note_taking.git_utils import check_if_behind_remote, pull_latest_changes


@click.command(help="""
Search for notes by vector similarity. This command allows you to find notes 
that are semantically similar to your query text. You can filter results by tag
and control how many results are returned.

Please note that vector search returns results based on semantic similarity, not exact matches.
It will return the top N most similar notes according to the embedding model, but some results
may not be relevant to your specific query. You should review the returned notes and select
only those that are actually relevant to your needs.
""")
@click.option("--query-text", required=True, help="Text to search for similarity matches")
@click.option("--tag", help="Optional tag to filter results. If not provided, searches across all tags.")
@click.option("--limit", default=10, help="Maximum number of results to return")
@click.option("--truncate", default=True, help="Whether or not to truncate the notes to 500 chars. Truncation enabled by default.")
def search_notes(query_text: str, tag: Optional[str] = None, limit: int = 10, truncate: bool = True):
    # Check Git repository status first (silently)
    is_behind, message = check_if_behind_remote()
    
    if is_behind:
        click.echo("Repository is behind remote. Pulling latest changes...")
        
        success, pull_message = pull_latest_changes()
        if success:
            click.echo("✓ Successfully pulled latest changes from GitHub")
        else:
            click.echo(f"Error syncing with GitHub: {pull_message}", err=True)
            click.echo("Proceeding with search using local database (may not include latest notes)")

    # Initialize the database with hard-coded db_name
    db = NotesDatabase(db_name="notes")
    
    try:
        # Generate embedding for the query text
        query_embedding = get_embedding(query_text)
        
        # Search for similar notes
        results = db.search_notes_by_similarity(
            query_embedding=query_embedding,
            limit=limit,
            tag_filter=tag
        )
        
        # Display results
        click.echo(f"\n--- Search Results ({len(results)} found) ---")
        
        if not results:
            click.echo("No matching notes found.")
            return
            
        for i, note in enumerate(results, 1):
            # Calculate similarity percentage (1 - distance) * 100
            similarity = (1 - note['distance']) * 100
            
            # Format the results
            click.echo(f"\n{i}. {note['title']} (Similarity: {similarity:.1f}%)")
            click.echo(f"Created: {note['created_at']}")
            if note.get('tags'):
                click.echo(f"Tags: {note['tags']}")
            
            click.echo("\nContent:")
            preview = note['content']
            if truncate:
                # Show a preview of the content (500 chars)
                if len(note['content']) > 500:
                    preview = preview[:500] + "..."
            click.echo(f"{preview}")

            click.echo("-" * 50)
            
    except Exception as e:
        click.echo(f"Error searching notes: {str(e)}", err=True)
    finally:
        # Close the database connection
        db.close()

if __name__ == "__main__":
    search_notes()

