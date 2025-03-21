import click
import duckdb
from src.note_taking.notes_database import NotesDatabase
from src.note_taking.git_utils import check_if_behind_remote, pull_latest_changes


@click.command(help="""
Execute arbitrary SQL queries against the notes database.

⚠️ FALLBACK ONLY: This tool should be used ONLY when the dedicated commands
(add-note, search-notes, get-notes-by-date-range, etc.) do not satisfy your specific need.

This provides direct SQL access to the notes database for advanced queries,
maintenance operations, and data exploration that cannot be accomplished with
the purpose-built tools. Results are displayed in a tabular format.

⚠️ CAUTION: This is a powerful tool that can modify or delete data. Table creation, modification, 
and deletion operations are not allowed for safety reasons.

Examples:
  execute-sql --query "SELECT * FROM notes LIMIT 5"
  execute-sql --query "SELECT t.name, COUNT(*) FROM tags t JOIN note_tags nt ON t.tag_id = nt.tag_id GROUP BY t.name"
""")
@click.option("--query", required=True, help="Valid DuckDB SQL query to execute against the database")
def notes_sql_backdoor(query: str):
    """Execute arbitrary SQL against the notes database."""
    # Always sync with remote
    click.echo("Checking for remote changes...")
    is_behind, message = check_if_behind_remote()
    
    if is_behind:
        click.echo("Repository is behind remote. Pulling latest changes...")
        
        success, pull_message = pull_latest_changes()
        if success:
            click.echo("✓ Successfully pulled latest changes from GitHub")
        else:
            click.echo(f"Error syncing with GitHub: {pull_message}", err=True)
            click.echo("Proceeding with local database (may not include latest notes)")
    else:
        click.echo("✓ Local database is up to date with remote")
    
    # Initialize the database
    db = NotesDatabase(db_name="notes")
    
    try:
        # Extract the query type using DuckDB's built-in parser
        statements = db.conn.extract_statements(query)
        if not statements:
            click.echo("Error: No valid SQL statement found.")
            return
            
        # Check if any statement type is not allowed
        allowed_types = [
            duckdb.StatementType.SELECT,
            duckdb.StatementType.INSERT,
            duckdb.StatementType.UPDATE,
            duckdb.StatementType.DELETE,
            duckdb.StatementType.EXPLAIN
        ]
        
        for stmt in statements:
            if stmt.type not in allowed_types:
                stmt_type = str(stmt.type).split('.')[-1]  # Get just the type name
                click.echo(f"Error: Statement type '{stmt_type}' is not allowed for safety reasons.")
                click.echo("Only SELECT, INSERT, UPDATE, DELETE, and EXPLAIN statements are permitted.")
                return
                
        # Check if any statement is a modifying statement
        is_readonly = all(stmt.type in [
            duckdb.StatementType.SELECT,
            duckdb.StatementType.EXPLAIN
        ] for stmt in statements)
        
        # Handle different query types based on statement type
        if is_readonly:
            # Execute and fetch results for read-only queries
            results = db.conn.execute(query).fetchall()
            
            # Get column names from the cursor description
            column_names = [col[0] for col in db.conn.description] if db.conn.description else []
            
            if not results:
                click.echo("Query executed successfully. No results returned.")
                return
            
            # Display results in a formatted table
            click.echo("\n--- Query Results ---")
            
            # Format column headers
            header_row = " | ".join(column_names)
            click.echo(header_row)
            click.echo("-" * len(header_row))
            
            # Format and display each row
            for row in results:
                # Convert each value to string with special handling for None and complex types
                formatted_row = []
                for value in row:
                    if value is None:
                        formatted_row.append("NULL")
                    elif isinstance(value, (list, dict)):
                        formatted_row.append(str(value))
                    else:
                        formatted_row.append(str(value))
                
                click.echo(" | ".join(formatted_row))
                
            # Show row count
            click.echo(f"\n{len(results)} row(s) returned")
            
        else:
            # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
            db.conn.execute(query)
            click.echo("Query executed successfully.")
            
    except Exception as e:
        click.echo(f"Error executing SQL: {str(e)}", err=True)
    finally:
        # Sync changes back to GitHub if we've made modifications
        if not is_readonly:
            db_path = db.get_db_path()
            click.echo("\n--- GitHub Synchronization ---")
            
            from src.note_taking.git_utils import sync_database_to_github
            # Truncate the query if needed for the commit message
            commit_msg = query.replace("\n", " ")[:50]
            if len(query) > 50:
                commit_msg += "..."
                
            success, message = sync_database_to_github(db_path, f"SQL: {commit_msg}")
            
            if success:
                click.echo("✓ Database successfully synced with GitHub")
                click.echo(f"✓ Changes committed and pushed to remote")
            else:
                click.echo(f"GitHub sync: {message}", err=True)
        
        # Close the database connection
        db.close()


if __name__ == "__main__":
    notes_sql_backdoor()
