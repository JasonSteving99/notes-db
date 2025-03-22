from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Optional


def generate_tag_colors(tags: List[str]) -> Dict[str, str]:
    """Generate a consistent color for each tag without hardcoding.
    
    Args:
        tags: List of unique tag names
        
    Returns:
        Dictionary mapping tag names to hex color codes
    """
    tag_colors = {}
    
    # Define a set of pleasant, accessible pastel colors
    base_hues = [
        15,    # warm orange
        45,    # amber
        75,    # yellow-green
        105,   # light green
        135,   # green
        165,   # teal
        195,   # light blue
        225,   # blue
        255,   # indigo
        285,   # purple
        315,   # magenta
        345    # pink
    ]
    
    # Derive colors based on tag names (deterministically)
    for i, tag in enumerate(sorted(tags)):
        # Use the tag name to pick a base hue (consistently)
        # This ensures the same tag always gets the same color
        tag_hash = sum(ord(c) for c in tag)
        hue_index = tag_hash % len(base_hues)
        base_hue = base_hues[hue_index]
        
        # Slightly adjust the hue to avoid exact collisions
        # But keep it close to ensure similar tags get similar colors
        hue = (base_hue + (i % 3) * 5) % 360
        
        # Light, gentle pastel (high lightness, low saturation)
        tag_colors[tag] = f"hsl({hue}, 70%, 90%)"
    
    return tag_colors


def organize_by_day(notes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Organize notes by day of the week."""
    days = defaultdict(list)
    
    for note in notes:
        # Parse the created_at timestamp
        if note.get("created_at"):
            created_at = datetime.fromisoformat(note["created_at"])
            day_name = created_at.strftime("%A")  # Get day name (Monday, Tuesday, etc.)
            days[day_name].append(note)
    
    # Sort by date (most recent first) within each day
    for day in days:
        days[day].sort(key=lambda x: x["created_at"], reverse=True)
    
    return dict(days)
