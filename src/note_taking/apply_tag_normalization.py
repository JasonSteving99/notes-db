import click
from src.note_taking.notes_database import NotesDatabase
from src.note_taking.git_utils import check_if_behind_remote, sync_database_to_github

@click.command(help="""
Apply a specific tag normalization to a set of notes.

This command normalizes tags for the specified notes by replacing or adding
a target tag and removing any specified tags to be replaced. All changes are 
committed to the database and synced with GitHub (if configured).

Example usage:
  apply-tag-normalization --note-ids 1,2,3 --keep-tag "python" --replace-tags "py,python3"
""")
@click.option("--note-ids", required=True, type=click.STRING,
              help="Comma-separated list of note IDs to normalize tags for")
@click.option("--keep-tag", required=True, type=click.STRING,
              help="The target tag to keep and ensure all notes have")
@click.option("--replace-tags", required=True, type=click.STRING,
              help="Comma-separated list of tags to remove and replace with the keep-tag")
def apply_tag_normalization(note_ids: str, keep_tag: str, replace_tags: str):
    """Apply a specified tag normalization to standardize tags."""
    # Check Git repository status first
    is_behind, message = check_if_behind_remote()
    
    if is_behind:
        click.echo("Error: Local repository is behind remote.", err=True)
        click.echo("Please run 'git pull' to update your local repository before applying changes.")
        click.echo("This is required to avoid database conflicts.")
        return
    
    # Parse inputs
    try:
        note_id_list = [int(id.strip()) for id in note_ids.split(',')]
        replace_tag_list = [tag.strip() for tag in replace_tags.split(',')]
    except ValueError:
        click.echo("Error: Invalid format for note IDs or tags. Use comma-separated values.", err=True)
        return
    
    if not note_id_list:
        click.echo("Error: No valid note IDs provided.", err=True)
        return
    
    # Initialize the database
    db = NotesDatabase(db_name="notes")
    
    try:
        # Display what will be updated
        click.echo("\n--- Tag Normalization Details ---")
        click.echo(f"Notes to update: {', '.join(map(str, note_id_list))}")
        click.echo(f"Tag to keep: '{keep_tag}'")
        click.echo(f"Tags to replace: {', '.join([f"'{tag}'" for tag in replace_tag_list])}")
        
        # Begin a transaction
        db.conn.execute("BEGIN TRANSACTION")
        
        try:
            # Track changes for reporting
            notes_updated = 0
            tags_removed = 0
            tags_added = 0
            
            # First, ensure primary tag exists in the database
            primary_tag_id_result = db.conn.execute("""
                SELECT tag_id FROM tags WHERE name = ?
            """, (keep_tag,)).fetchone()
            
            if primary_tag_id_result is None:
                # Create the primary tag if it doesn't exist
                primary_tag_id_result = db.conn.execute("""
                    INSERT INTO tags (name)
                    VALUES (?)
                    RETURNING tag_id
                """, (keep_tag,)).fetchone()
            
            primary_tag_id = primary_tag_id_result[0]
            
            # Process each note
            for note_id in note_id_list:
                # Verify note exists
                note_exists = db.conn.execute("""
                    SELECT 1 FROM notes WHERE note_id = ?
                """, (note_id,)).fetchone()
                
                if not note_exists:
                    click.echo(f"Warning: Note ID {note_id} not found. Skipping.")
                    continue
                
                # Get current tags for this note
                current_tags_result = db.conn.execute("""
                    SELECT t.tag_id, t.name
                    FROM note_tags nt
                    JOIN tags t ON nt.tag_id = t.tag_id
                    WHERE nt.note_id = ?
                """, (note_id,)).fetchall()
                
                current_tag_ids = [row[0] for row in current_tags_result]
                current_tag_names = [row[1] for row in current_tags_result]
                
                # Check if primary tag already exists for this note
                has_primary_tag = keep_tag in current_tag_names
                
                # Get tags to remove
                tags_to_remove = [tag_id for tag_id, tag_name in zip(current_tag_ids, current_tag_names) 
                               if tag_name in replace_tag_list]
                
                # Remove secondary tags
                if tags_to_remove:
                    for tag_id in tags_to_remove:
                        db.conn.execute("""
                            DELETE FROM note_tags 
                            WHERE note_id = ? AND tag_id = ?
                        """, (note_id, tag_id))
                    
                    tags_removed += len(tags_to_remove)
                
                # Add primary tag if it doesn't exist
                if not has_primary_tag:
                    db.conn.execute("""
                        INSERT INTO note_tags (note_id, tag_id)
                        VALUES (?, ?)
                    """, (note_id, primary_tag_id))
                    
                    tags_added += 1
                
                notes_updated += 1
            
            # Commit the transaction
            db.conn.execute("COMMIT")
            
            # Display results
            click.echo("\n--- Tag Normalization Complete ---")
            click.echo(f"Notes updated: {notes_updated}")
            click.echo(f"Tags removed: {tags_removed}")
            click.echo(f"Tags added: {tags_added}")
            
            # Sync with GitHub
            db_path = db.get_db_path()
            click.echo("\n--- GitHub Synchronization ---")
            
            success, message = sync_database_to_github(db_path, "Normalize tags")
            if success:
                click.echo("Database successfully synced with GitHub")
                click.echo("✓ Committed with message: 'Normalize tags'")
                click.echo("✓ Pushed changes to GitHub")
            else:
                click.echo(f"GitHub sync: {message}", err=True)
            
        except Exception as e:
            # Rollback in case of error
            db.conn.execute("ROLLBACK")
            click.echo(f"Error applying tag normalizations: {str(e)}", err=True)
            click.echo("No changes were made to the database.")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
    finally:
        # Close the database connection
        db.close()


if __name__ == "__main__":
    apply_tag_normalization()
