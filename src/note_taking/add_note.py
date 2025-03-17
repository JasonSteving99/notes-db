import click
from datetime import datetime, timedelta
from src.note_taking.embed_content import get_embedding
from src.note_taking.notes_database import NotesDatabase
from src.note_taking.git_utils import check_if_behind_remote, pull_latest_changes, sync_database_to_github

@click.command(help="""
This is a simple note-taking tool that stores text notes in databases. Each note has a title, 
content, and optional tag for categorization. The tool maintains statistics about total notes, recent
additions, and tag usage. Use it to organize information like meeting notes, project ideas, personal
reminders, or any text content you want to store in a structured way for later reference.
""")
@click.option("--title", required=True, help="Title of the note.")
@click.option("--content", required=True, help="Content of the note.")
@click.option("--tag", help="Tag for the note.")
def add_note(title: str, content: str, tag: str | None):
    """Add a new note to the database."""
    # First, check if we're behind the remote repository
    click.echo("Checking Git repository status...")
    is_behind, message = check_if_behind_remote()
    
    if is_behind:
        click.echo(f"Error: {message}", err=True)
        click.echo("Please run 'git pull' to update your local repository before adding a note.")
        click.echo("This is required to avoid database conflicts.")
        return
    
    # If not behind, proceed to add the note
    click.echo("Git repository is up to date.")
    
    # Create an embedding.
    embedding = get_embedding(content)

    # Initialize the database.
    db = NotesDatabase(db_name="notes")

    try:
        # Add the note
        note_id = db.add_note(title=title, content=content, embedding=embedding, tags=[tag] if tag else [])
        click.echo(f"Note added successfully with ID: {note_id}")

        # Display database statistics
        display_database_stats(db)
        
        # Sync with GitHub
        db_path = db.get_db_path()
        click.echo("\n--- GitHub Synchronization ---")
        
        success, message = sync_database_to_github(db_path, title)
        if success:
            click.echo("Database successfully synced with GitHub")
            click.echo(f"✓ Committed with message: 'Add note: {title}'")
            click.echo("✓ Pushed changes to GitHub")
        else:
            click.echo(f"GitHub sync: {message}", err=True)
            if message == "No changes to commit":
                click.echo("Note has been added to the database but no Git changes were needed.")
            else:
                click.echo("Possible issues:")
                click.echo("  - Not in a Git repository")
                click.echo("  - Database is outside the Git repository")
                click.echo("  - Git remote is not configured")
                click.echo("  - Authentication issues with remote repository")
            
    except Exception as e:
        click.echo(f"Error adding note: {str(e)}", err=True)
    finally:
        # Close the database connection
        db.close()

def display_database_stats(db: NotesDatabase):
    """Display useful statistics about the notes database."""
    click.echo("\n--- Database Statistics ---")

    # Total number of notes
    total_notes = db.conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    click.echo(f"Total notes: {total_notes}")

    # Notes created in the last week
    one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    recent_notes = db.conn.execute(
        "SELECT COUNT(*) FROM notes WHERE created_at >= ?",
        (one_week_ago,)
    ).fetchone()[0]
    click.echo(f"Notes created in the last 7 days: {recent_notes}")

    # Total number of unique tags
    total_tags = db.conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    click.echo(f"Total unique tags: {total_tags}")

    # List all tags with counts
    if total_tags > 0:
        tag_counts = db.conn.execute("""
            SELECT t.name, COUNT(nt.note_id) as note_count
            FROM tags t
            LEFT JOIN note_tags nt ON t.tag_id = nt.tag_id
            GROUP BY t.name
            ORDER BY note_count DESC, t.name
        """).fetchall()

        click.echo("\nTag usage:")
        for tag_name, count in tag_counts:
            click.echo(f"  - {tag_name}: {count} note(s)")

    click.echo("---------------------------")

if __name__ == "__main__":
    add_note()

