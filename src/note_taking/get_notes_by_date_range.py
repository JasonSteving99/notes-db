import click
from datetime import datetime, timedelta
from typing import List
from src.note_taking.notes_database import NotesDatabase
from src.note_taking.git_utils import check_if_behind_remote, pull_latest_changes


def parse_time_range(value: str, unit: str) -> datetime:
    """
    Parse a time range value and unit to calculate the start date.
    
    Args:
        value: Numeric value for the time range
        unit: Unit of time (days, weeks, months, years)
        
    Returns:
        datetime representing the start of the time range
        
    Raises:
        ValueError: If the unit is not supported
    """
    try:
        amount = int(value)
    except ValueError:
        raise ValueError(f"Value must be an integer: {value}")
        
    now = datetime.now()
    
    if unit == "days":
        return now - timedelta(days=amount)
    elif unit == "weeks":
        return now - timedelta(weeks=amount)
    elif unit == "months":
        # Approximate a month as 30 days
        return now - timedelta(days=amount * 30)
    elif unit == "years":
        # Approximate a year as 365 days
        return now - timedelta(days=amount * 365)
    else:
        raise ValueError(f"Unsupported time unit: {unit}. Use days, weeks, months, or years.")


@click.command(help="""
Retrieve notes created within a specified time range.

This command allows you to find notes created within a certain time period from now.
You can specify the time range in days, weeks, months, or years, and optionally filter
by tag. Results can be limited and sorted by creation date.

Examples:
    get-notes-by-date-range --time-range 7 --unit days
    get-notes-by-date-range --time-range 2 --unit weeks --tag programming
""")
@click.option("--time-range", required=True, type=int, help="How far back to search for notes")
@click.option("--unit", required=True, type=click.Choice(['days', 'weeks', 'months', 'years']), 
              help="Unit of time for the range")
@click.option("--tag", help="Optional tag to filter results")
@click.option("--limit", default=50, help="Maximum number of results to return")
@click.option("--sort", default="newest", type=click.Choice(['newest', 'oldest']), 
              help="Sort order for results")
@click.option("--truncate", default=True, help="Whether to truncate note content in output")
def get_notes_by_date_range(time_range: int, unit: str, tag: str | None = None, 
                           limit: int = 50, sort: str = "newest", truncate: bool = True):
    """Retrieve notes created within a specified time range."""
    # Check Git repository status
    is_behind, message = check_if_behind_remote()
    
    if is_behind:
        click.echo("Repository is behind remote. Pulling latest changes...")
        
        success, pull_message = pull_latest_changes()
        if success:
            click.echo("✓ Successfully pulled latest changes from GitHub")
        else:
            click.echo(f"Error syncing with GitHub: {pull_message}", err=True)
            click.echo("Proceeding with local database (may not include latest notes)")

    # Calculate the start date for the query
    try:
        start_date = parse_time_range(time_range, unit)
        start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        return

    # Initialize the database
    db = NotesDatabase(db_name="notes")
    
    try:
        # Construct the query
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
        """
        
        params = [start_date_str]
        
        # Add tag filtering if specified
        if tag:
            query += """
                AND n.note_id IN (
                    SELECT nt.note_id 
                    FROM note_tags nt 
                    JOIN tags t ON nt.tag_id = t.tag_id 
                    WHERE t.name = ?
                )
            """
            params.append(tag)
        
        # Add sorting
        if sort == "newest":
            query += " ORDER BY n.created_at DESC"
        else:
            query += " ORDER BY n.created_at ASC"
        
        # Add limit
        query += " LIMIT ?"
        params.append(limit)
        
        # Execute the query
        results = db.conn.execute(query, params).fetchall()
        
        # Convert to list of dictionaries
        column_names = ["note_id", "title", "content", "created_at", "tags"]
        notes = [dict(zip(column_names, row)) for row in results]
        
        # Display the time range description
        if unit == "days" and time_range == 1:
            range_desc = "the past day"
        elif unit == "weeks" and time_range == 1:
            range_desc = "the past week"
        elif unit == "months" and time_range == 1:
            range_desc = "the past month"
        elif unit == "years" and time_range == 1:
            range_desc = "the past year"
        else:
            range_desc = f"the past {time_range} {unit}"
        
        # Add tag info if applicable
        filter_desc = f" with tag '{tag}'" if tag else ""
        
        # Display results
        click.echo(f"\n--- Notes from {range_desc}{filter_desc} ({len(notes)} found) ---")
        
        if not notes:
            click.echo("No notes found in the specified time range.")
            return
            
        for i, note in enumerate(notes, 1):
            # Format the results
            created_date = note['created_at']
            date_str = created_date.strftime("%Y-%m-%d %H:%M")
            
            click.echo(f"\n{i}. {note['title']} (ID: {note['note_id']})")
            click.echo(f"Created: {date_str}")
            if note.get('tags'):
                click.echo(f"Tags: {note['tags']}")
            
            click.echo("\nContent:")
            preview = note['content']
            if truncate:
                # Show a preview of the content (300 chars)
                if len(note['content']) > 300:
                    preview = preview[:300] + "..."
            click.echo(f"{preview}")
            
            click.echo("-" * 50)
            
    except Exception as e:
        click.echo(f"Error retrieving notes: {str(e)}", err=True)
    finally:
        # Close the database connection
        db.close()


if __name__ == "__main__":
    get_notes_by_date_range()
