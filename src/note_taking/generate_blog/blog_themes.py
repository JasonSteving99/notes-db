import click
from collections import defaultdict
from typing import List, Dict, Any

from src.note_taking.embed_content import get_embedding


def extract_themes(notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract themes based on note content and tags using semantic analysis."""
    
    # First, do a basic tag-based grouping
    tag_notes = defaultdict(list)
    
    for note in notes:
        tags = note.get("tags", "").split(", ") if note.get("tags") else []
        for tag in tags:
            if tag:
                tag_notes[tag].append(note)
    
    # Generate themes based on tag groups
    themes = []
    
    for tag, tag_note_list in tag_notes.items():
        if len(tag_note_list) >= 2:  # Only consider tags with at least 2 notes
            # Get summaries of content for these notes
            note_excerpts = []
            for note in tag_note_list[:3]:  # Take up to 3 notes for the description
                content = note["content"]
                if len(content) > 100:
                    excerpt = content[:100] + "..."
                else:
                    excerpt = content
                note_excerpts.append(excerpt)
            
            # Create a more descriptive theme summary
            description = f"There were {len(tag_note_list)} notes related to {tag.replace('-', ' ')}. "
            if note_excerpts:
                description += f"These included topics like: {'; '.join(note['title'] for note in tag_note_list[:3])}"
            
            theme = {
                "name": f"{tag.replace('-', ' ').title()} Focus",
                "description": description,
                "notes": [note["id"] for note in tag_note_list],
                "tag": tag
            }
            themes.append(theme)
    
    # Sort themes by number of notes (descending)
    themes.sort(key=lambda x: len(x["notes"]), reverse=True)
    
    return themes
