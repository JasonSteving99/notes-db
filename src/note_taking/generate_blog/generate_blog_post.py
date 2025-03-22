import click
import os
from datetime import datetime, timedelta

from src.note_taking.notes_database import NotesDatabase
from src.note_taking.git_utils import check_if_behind_remote, pull_latest_changes
from src.note_taking.generate_blog.blog_insights import generate_insights
from src.note_taking.generate_blog.blog_themes import extract_themes
from src.note_taking.generate_blog.blog_utils import organize_by_day
from src.note_taking.generate_blog.blog_template import generate_html


@click.command(help="""
Generate an interactive blog post from notes collected over the past week.

This tool compiles your recent notes into an engaging, interactive blog
post, written in third-person perspective by an AI. The output is a
standalone HTML file with interactive elements, including hover-over
citations that display the full content of referenced notes.

The blog post integrates concepts from multiple notes and organizes them
into a visually appealing presentation. Notes are filtered to only include
those created in the past 7 days.
""")
@click.option("--output-path", help="Path where the HTML file will be saved (defaults to 'blog_post.html' in the script directory)")
@click.option("--api-key", help="Gemini API key (uses GEMINI_API_KEY env var if not provided)")
@click.option("--git-sync", type=click.BOOL, default=True, help="Whether or not to keep database synced up automatically.")
def generate_blog_post(output_path: str | None = None, api_key: str | None = None, git_sync: bool = True):
    """Generate an interactive weekly blog post from the past week's notes."""
    # Check for API key in environment if not provided
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    
    if git_sync:
        # Check Git repository status first
        is_behind, message = check_if_behind_remote()
        
        if is_behind:
            click.echo("Repository is behind remote. Pulling latest changes...")
            
            success, pull_message = pull_latest_changes()
            if success:
                click.echo("✓ Successfully pulled latest changes from GitHub")
            else:
                click.echo(f"Error syncing with GitHub: {pull_message}", err=True)
                click.echo("Proceeding with local database (may not include latest notes)")

    # Initialize the database
    db = NotesDatabase(db_name="notes")
    
    try:
        # Calculate one week ago from today
        one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Get all notes from the past week
        query = """
            SELECT 
                n.note_id, 
                n.title, 
                n.content, 
                n.created_at,
                (SELECT STRING_AGG(t.name, ', ') 
                 FROM note_tags nt 
                 JOIN tags t ON nt.tag_id = t.tag_id 
                 WHERE nt.note_id = n.note_id) AS tags
            FROM notes n
            WHERE n.created_at >= ?
            ORDER BY n.created_at DESC
        """
        
        results = db.conn.execute(query, [one_week_ago]).fetchall()
        
        # Convert to list of dictionaries and process dates
        column_names = ["id", "title", "content", "created_at", "tags"]
        notes = []
        
        for row in results:
            note_dict = dict(zip(column_names, row))
            # Convert datetime to string format
            note_dict["created_at"] = note_dict["created_at"].isoformat() if note_dict["created_at"] else None
            notes.append(note_dict)
        
        if not notes:
            click.echo("No notes found in the past week. Cannot generate blog post.")
            return
            
        click.echo(f"Found {len(notes)} notes from the past week.")
        
        # Generate insights and summary from notes
        if api_key:
            click.echo("Using Gemini API to generate insights...")
            insights = generate_insights(notes, api_key)
        else:
            click.echo("No Gemini API key found. Using basic analysis...")
            insights = generate_insights(notes)
        
        # Generate themes from note tags
        themes = extract_themes(notes)
        
        # Organize notes by day
        daily_notes = organize_by_day(notes)
        
        # Create HTML content
        html_content = generate_html(notes, insights, themes, daily_notes)
        
        # Determine output path
        if not output_path:
            # Use the script directory by default
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(script_dir, "blog_post.html")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Write HTML to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        click.echo(f"Blog post successfully generated at: {output_path}")
        click.echo("Open this file in your browser to view your weekly summary.")
        
    except Exception as e:
        click.echo(f"Error generating blog post: {str(e)}", err=True)
    finally:
        # Close the database connection
        db.close()


if __name__ == "__main__":
    generate_blog_post()
