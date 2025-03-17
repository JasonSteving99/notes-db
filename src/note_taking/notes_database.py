import duckdb
import os
from datetime import datetime
from typing import List, Optional, Union, Tuple, Any
from pathlib import Path

class NotesDatabase:
    def __init__(self, db_name: str = "notes") -> None:
        # Determine the directory where the class file is located
        self.class_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        
        # Create database directory if it doesn't exist
        db_dir = self.class_dir / "database"
        os.makedirs(db_dir, exist_ok=True)
        
        # Construct full path to the database file, adding the .duckdb extension
        self.db_path = db_dir / f"{db_name}.duckdb"
        
        self.conn = duckdb.connect(str(self.db_path))
        self._init_db()
        
    def _init_db(self) -> None:
        """Initialize the database schema if it doesn't exist."""
        # Path to the schema SQL file
        schema_path = self.class_dir / "notes_schema.sql"
        
        # Read the schema file
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute the schema SQL
        self.conn.execute(schema_sql)
    
    def add_note(self, 
                title: str, 
                content: str, 
                embedding: List[float], 
                tags: Optional[List[str]] = None) -> int:
        """
        Add a new note with tags in a single transaction.
        
        Args:
            title: The note title
            content: The note content (required)
            embedding: A 3072-dimensional float array representing the note embedding (required)
            tags: List of tag names
        
        Returns:
            The ID of the newly created note
        
        Raises:
            ValueError: If embedding is not the correct dimension
        """
        # Only keep the embedding length check
        if len(embedding) != 3072:
            raise ValueError("Embedding must be exactly 3072 dimensions")
            
        # Begin a transaction
        self.conn.execute("BEGIN TRANSACTION")
        
        try:
            # Insert the note and get the ID using RETURNING
            result = self.conn.execute("""
                INSERT INTO notes (title, content, embedding) 
                VALUES (?, ?, ?)
                RETURNING note_id
            """, (title, content, embedding)).fetchone()
            
            note_id = result[0]
            
            # Process tags if provided
            if tags:
                for tag_name in tags:
                    # First try to get the tag ID if it exists
                    result = self.conn.execute("""
                        SELECT tag_id FROM tags WHERE name = ?
                    """, (tag_name,)).fetchone()
        
                    # If the tag doesn't exist, create it
                    if result is None:
                        result = self.conn.execute("""
                            INSERT INTO tags (name)
                            VALUES (?)
                            RETURNING tag_id
                        """, (tag_name,)).fetchone()

                    tag_id = result[0]
                    
                    # Link the note to the tag
                    self.conn.execute("""
                        INSERT INTO note_tags (note_id, tag_id) 
                        VALUES (?, ?)
                    """, (note_id, tag_id))
            
            # Commit the transaction
            self.conn.execute("COMMIT")
            return note_id
            
        except Exception as e:
            # Rollback in case of error
            self.conn.execute("ROLLBACK")
            raise e


    def search_notes_by_similarity(self, 
                              query_embedding: List[float], 
                              limit: int = 10, 
                              tag_filter: Optional[str] = None) -> List[dict]:
        """
        Search for similar notes using vector search with optional tag filtering.
        
        Args:
            query_embedding: A 3072-dimensional float array representing the query
            limit: Maximum number of results to return (default: 10)
            tag_filter: Optional tag name to filter results
            
        Returns:
            List of matching notes with similarity scores and associated tags
        
        Raises:
            ValueError: If embedding is not the correct dimension
        """
        if len(query_embedding) != 3072:
            raise ValueError("Query embedding must be exactly 3072 dimensions")
    
        # Base query with vector search and tag retrieval
        query = """
            SELECT 
                n.note_id, 
                n.title, 
                n.content, 
                n.created_at,
                n.embedding <=> ? AS distance,
                (SELECT STRING_AGG(t.name, ', ') 
                 FROM note_tags nt 
                 JOIN tags t ON nt.tag_id = t.tag_id 
                 WHERE nt.note_id = n.note_id) AS tags
            FROM notes n
        """
    
        params = [query_embedding]
    
        # Add tag filtering if specified
        if tag_filter:
            query += """
                WHERE n.note_id IN (
                    SELECT nt.note_id 
                    FROM note_tags nt 
                    JOIN tags t ON nt.tag_id = t.tag_id 
                    WHERE t.name = ?
                )
            """
            params.append(tag_filter)
    
        # Add ordering and limit
        query += """
            ORDER BY distance
            LIMIT ?
        """
        params.append(limit)
    
        # Execute the query
        results = self.conn.execute(query, params).fetchall()
    
        # Convert to list of dictionaries
        column_names = ["note_id", "title", "content", "created_at", "distance", "tags"]
        return [dict(zip(column_names, row)) for row in results]

    
    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()

    def get_db_path(self) -> Path:
        """Get the absolute path to the database file."""
        return self.db_path.absolute()

