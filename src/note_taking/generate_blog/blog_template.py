import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Any

from src.note_taking.generate_blog.blog_utils import generate_tag_colors


def generate_html(notes: List[Dict[str, Any]], 
                insights: Dict[str, Any], 
                themes: List[Dict[str, Any]], 
                daily_notes: Dict[str, List[Dict[str, Any]]]) -> str:
    """Generate the HTML content for the blog post."""
    
    # Convert notes to JSON for JavaScript
    notes_json = json.dumps({"notes": notes}, indent=2)
    
    # Get all unique tags from notes
    all_tags = set()
    for note in notes:
        tags = note.get("tags", "").split(", ") if note.get("tags") else []
        all_tags.update(tag for tag in tags if tag)
    
    # Generate colors for all tags
    tag_colors = generate_tag_colors(list(all_tags))
    
    # Count notes by day for the timeline
    timeline_data = {}
    for day, day_notes in daily_notes.items():
        timeline_data[day] = len(day_notes)
    
    # Sort days of the week properly
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    timeline_sorted = {day: timeline_data.get(day, 0) for day in days_order if day in timeline_data}
    
    # Count notes by tag for the tag visualization
    tag_counts = defaultdict(int)
    for note in notes:
        tags = note.get("tags", "").split(", ") if note.get("tags") else []
        for tag in tags:
            if tag:
                tag_counts[tag] += 1
    
    # Convert insights to HTML
    accomplishments_html = "".join([f"<li>{acc}</li>" for acc in insights.get("key_accomplishments", [])])
    themes_html = "".join([f"<li>{theme}</li>" for theme in insights.get("themes", [])[:3]])
    
    # Create the HTML template with properly escaped JavaScript
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Summary - {datetime.now().strftime('%B %d, %Y')}</title>
    <style>
        :root {{
            --primary-color: #0056b3;
            --secondary-color: #6c757d;
            --accent-color: #ffc107;
            --light-bg: #f8f9fa;
            --dark-bg: #343a40;
            --text-color: #333;
            --light-text: #f8f9fa;
            --border-color: #dee2e6;
            --shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            --transition: all 0.3s ease;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--light-bg);
            color: var(--text-color);
            line-height: 1.6;
        }}

        #app {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            box-shadow: var(--shadow);
        }}

        header {{
            text-align: center;
            padding: 20px 0;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 20px;
        }}

        header h1 {{
            margin: 0;
            color: var(--primary-color);
            font-size: 2.5em;
        }}

        header p {{
            color: var(--secondary-color);
            font-size: 1.2em;
            margin: 10px 0 0;
        }}

        section {{
            margin-bottom: 30px;
            padding: 20px;
            border-radius: 5px;
            background-color: white;
            box-shadow: var(--shadow);
        }}

        h2, h3 {{
            color: var(--primary-color);
        }}

        h2 {{
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 10px;
            margin-top: 0;
        }}

        /* Weekly Summary Section */
        #weekly-summary {{
            background-color: var(--light-bg);
        }}

        /* Note Styles */
        .note {{
            border: 1px solid var(--border-color);
            margin-bottom: 15px;
            border-radius: 5px;
            overflow: hidden;
            transition: var(--transition);
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}

        .note:hover {{
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}

        .note-header {{
            padding: 15px;
            background-color: var(--light-bg);
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            border-bottom: 1px solid var(--border-color);
        }}

        .note-header h3 {{
            margin: 0;
            font-size: 1.2em;
            flex: 1;
        }}

        .note-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.5s ease;
            padding: 0 15px;
        }}

        .note.expanded .note-content {{
            max-height: 2000px;
            padding: 15px;
        }}

        .note-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}

        .tag {{
            padding: 3px 8px;
            border-radius: 15px;
            font-size: 0.8em;
            white-space: nowrap;
        }}

        .note-meta {{
            font-size: 0.85em;
            color: var(--secondary-color);
            margin-top: 5px;
        }}

        /* Timeline Styles */
        #timeline-chart {{
            height: 200px;
            margin-top: 20px;
        }}

        /* Tags Chart */
        #tags-chart {{
            height: 300px;
            margin-top: 20px;
        }}

        /* Daily Summary Styles */
        .day-summary {{
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 5px;
            background-color: var(--light-bg);
        }}

        .day-summary h3 {{
            margin-top: 0;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 5px;
        }}

        /* Control Buttons */
        .controls {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }}

        button {{
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            transition: var(--transition);
        }}

        button:hover {{
            background-color: #004494;
        }}

        /* Markdown Styles */
        .markdown-body {{
            color: var(--text-color);
        }}

        .markdown-body h1 {{
            font-size: 1.8em;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.3em;
        }}

        .markdown-body h2 {{
            font-size: 1.5em;
        }}

        .markdown-body h3 {{
            font-size: 1.2em;
        }}

        .markdown-body code {{
            background-color: #f6f8fa;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: monospace;
        }}

        .markdown-body pre {{
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }}

        .markdown-body blockquote {{
            border-left: 4px solid var(--border-color);
            padding-left: 16px;
            color: var(--secondary-color);
            margin-left: 0;
        }}

        /* Theme Badge */
        .theme-badge {{
            display: inline-block;
            padding: 5px 10px;
            margin: 5px;
            border-radius: 15px;
            background-color: var(--light-bg);
            color: var(--text-color);
            font-size: 0.9em;
            cursor: pointer;
            transition: var(--transition);
        }}

        .theme-badge:hover {{
            transform: translateY(-2px);
        }}
        
        /* Theme Badge Count */
        .theme-badge-count {{
            display: inline-block;
            background-color: var(--primary-color);
            color: white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            text-align: center;
            line-height: 20px;
            margin-left: 5px;
            font-size: 0.8em;
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            #app {{
                padding: 10px;
            }}
            
            section {{
                padding: 15px;
            }}
            
            header h1 {{
                font-size: 2em;
            }}
        }}

        /* Tag Group Styles */
        .tag-group {{
            margin-bottom: 30px;
        }}
    </style>
</head>
<body>
    <div id="app">
        <header>
            <h1>Weekly Notes Summary</h1>
            <p>{datetime.now().strftime('%B %d')} - {(datetime.now() - timedelta(days=7)).strftime('%B %d, %Y')}</p>
        </header>

        <section id="weekly-summary">
            <h2>Weekly Overview</h2>
            <p>{insights["summary"].strip()}</p>
            
            <div class="summary-details">
                <div>
                    <h3>Key Accomplishments</h3>
                    <ul>
                        {accomplishments_html}
                    </ul>
                </div>
                
                <div>
                    <h3>Emerging Themes</h3>
                    <ul>
                        {themes_html}
                    </ul>
                </div>
            </div>
        </section>

        <section id="themes-section">
            <h2>Key Themes</h2>
            <div id="themes-container"></div>
        </section>

        <section id="timeline">
            <h2>Activity Timeline</h2>
            <div id="timeline-chart"></div>
        </section>

        <section id="tags">
            <h2>Topic Distribution</h2>
            <div id="tags-chart"></div>
        </section>

        <section id="notes-section">
            <h2>This Week's Notes</h2>
            <div class="controls">
                <button id="expand-all">Expand All</button>
                <button id="collapse-all">Collapse All</button>
                <button id="sort-by-date">Sort by Date</button>
                <button id="group-by-tag">Group by Tag</button>
            </div>
            <div id="notes-container"></div>
        </section>

        <section id="daily-summaries">
            <h2>Daily Breakdown</h2>
            <div id="daily-container"></div>
        </section>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Data from Python
        const notesData = {notes_json};
        const tagColors = {json.dumps(tag_colors)};
        const timelineData = {json.dumps(timeline_sorted)};
        const tagCounts = {json.dumps(dict(tag_counts))};
        const themes = {json.dumps(themes)};
        
        // DOM Elements
        const notesContainer = document.getElementById('notes-container');
        const dailyContainer = document.getElementById('daily-container');
        const themesContainer = document.getElementById('themes-container');
        const expandAllButton = document.getElementById('expand-all');
        const collapseAllButton = document.getElementById('collapse-all');
        const sortByDateButton = document.getElementById('sort-by-date');
        const groupByTagButton = document.getElementById('group-by-tag');
        
        // State tracking
        let currentSort = 'date-desc';
        let currentGroup = 'none';
        
        // Initialize
        function init() {{
            renderThemes();
            renderNotes();
            renderDailySummaries();
            renderTimelineChart();
            renderTagsChart();
            setupEventListeners();
        }}
        
        // Render themes badges
        function renderThemes() {{
            themesContainer.innerHTML = '';
            
            themes.forEach(theme => {{
                const themeEl = document.createElement('div');
                themeEl.classList.add('theme-badge');
                themeEl.style.backgroundColor = tagColors[theme.tag] || '#f0f0f0';
                themeEl.innerHTML = `
                    <span>${{theme.name}}</span>
                    <span class="theme-badge-count">${{theme.notes.length}}</span>
                `;
                
                // Add click event to filter notes by this theme
                themeEl.addEventListener('click', () => {{
                    filterNotesByTag(theme.tag);
                }});
                
                themesContainer.appendChild(themeEl);
            }});
        }}
        
        // Filter notes by tag
        function filterNotesByTag(tag) {{
            const notes = document.querySelectorAll('.note');
            
            notes.forEach(note => {{
                const noteTags = note.getAttribute('data-tags').split(',');
                if (noteTags.includes(tag)) {{
                    note.style.display = 'block';
                }} else {{
                    note.style.display = 'none';
                }}
            }});
            
            // Update UI to indicate filtering is active
            document.querySelectorAll('.theme-badge').forEach(badge => {{
                badge.style.opacity = badge.textContent.includes(tag) ? 1 : 0.5;
            }});
            
            // Add reset button if not already present
            if (!document.getElementById('reset-filter')) {{
                const resetButton = document.createElement('button');
                resetButton.id = 'reset-filter';
                resetButton.textContent = 'Show All Notes';
                resetButton.addEventListener('click', resetFilter);
                document.querySelector('.controls').appendChild(resetButton);
            }}
        }}
        
        // Reset filter to show all notes
        function resetFilter() {{
            const notes = document.querySelectorAll('.note');
            notes.forEach(note => note.style.display = 'block');
            
            // Reset theme badges
            document.querySelectorAll('.theme-badge').forEach(badge => {{
                badge.style.opacity = 1;
            }});
            
            // Remove reset button
            const resetButton = document.getElementById('reset-filter');
            if (resetButton) {{
                resetButton.remove();
            }}
        }}
        
        // Render the notes
        function renderNotes() {{
            notesContainer.innerHTML = '';
            
            notesData.notes.forEach(note => {{
                const noteDiv = document.createElement('div');
                noteDiv.classList.add('note');
                noteDiv.setAttribute('data-id', note.id);
                noteDiv.setAttribute('data-date', note.created_at);
                noteDiv.setAttribute('data-tags', note.tags || '');
                
                const created = new Date(note.created_at);
                const formattedDate = created.toLocaleDateString('en-US', {{ 
                    weekday: 'short',
                    month: 'short', 
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                }});
                
                // Create the note header
                const noteHeader = document.createElement('div');
                noteHeader.classList.add('note-header');
                
                // Create the note title
                const titleEl = document.createElement('h3');
                titleEl.textContent = note.title;
                
                // Create tags element
                const tagsEl = document.createElement('div');
                tagsEl.classList.add('note-tags');
                
                // Add tags if any
                if (note.tags) {{
                    note.tags.split(',').forEach(tag => {{
                        tag = tag.trim();
                        if (tag) {{
                            const tagEl = document.createElement('span');
                            tagEl.classList.add('tag');
                            tagEl.textContent = tag;
                            tagEl.style.backgroundColor = tagColors[tag] || '#f0f0f0';
                            
                            // Make tags clickable for filtering
                            tagEl.addEventListener('click', (e) => {{
                                e.stopPropagation(); // Don't toggle note expansion
                                filterNotesByTag(tag);
                            }});
                            
                            tagsEl.appendChild(tagEl);
                        }}
                    }});
                }}
                
                // Add elements to header
                noteHeader.appendChild(titleEl);
                noteHeader.appendChild(tagsEl);
                
                // Create meta information element
                const metaEl = document.createElement('div');
                metaEl.classList.add('note-meta');
                metaEl.textContent = `Created: ${{formattedDate}}`;
                
                // Create the content container
                const contentEl = document.createElement('div');
                contentEl.classList.add('note-content');
                contentEl.classList.add('markdown-body');
                contentEl.innerHTML = marked.parse(note.content);
                
                // Add everything to the note
                noteDiv.appendChild(noteHeader);
                noteDiv.appendChild(metaEl);
                noteDiv.appendChild(contentEl);
                
                // Toggle expansion when header is clicked
                noteHeader.addEventListener('click', () => {{
                    noteDiv.classList.toggle('expanded');
                }});
                
                notesContainer.appendChild(noteDiv);
            }});
        }}
        
        // Render daily summaries
        function renderDailySummaries() {{
            dailyContainer.innerHTML = '';
            
            // Group notes by day
            const days = {{}};
            notesData.notes.forEach(note => {{
                const created = new Date(note.created_at);
                const day = created.toLocaleDateString('en-US', {{ weekday: 'long' }});
                
                if (!days[day]) {{
                    days[day] = [];
                }}
                
                days[day].push(note);
            }});
            
            // Sort days in order (Monday to Sunday)
            const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
            
            dayOrder.forEach(day => {{
                if (days[day] && days[day].length > 0) {{
                    const dayDiv = document.createElement('div');
                    dayDiv.classList.add('day-summary');
                    
                    const heading = document.createElement('h3');
                    heading.textContent = `${{day}} (${{days[day].length}} notes)`;
                    
                    const summary = document.createElement('p');
                    
                    // Create a simple summary of the day's activities
                    const topics = new Set();
                    days[day].forEach(note => {{
                        if (note.tags) {{
                            note.tags.split(',').forEach(tag => {{
                                topics.add(tag.trim());
                            }});
                        }}
                    }});
                    
                    const topicsList = Array.from(topics).filter(t => t).join(', ');
                    
                    summary.textContent = `On ${{day}}, you wrote about ${{topics.size}} topics: ${{topicsList || 'various subjects'}}.`;
                    
                    dayDiv.appendChild(heading);
                    dayDiv.appendChild(summary);
                    dailyContainer.appendChild(dayDiv);
                }}
            }});
        }}
        
        // Render the timeline chart
        function renderTimelineChart() {{
            const ctx = document.createElement('canvas');
            document.getElementById('timeline-chart').appendChild(ctx);
            
            const days = Object.keys(timelineData);
            const counts = Object.values(timelineData);
            
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: days,
                    datasets: [{{
                        label: 'Number of Notes',
                        data: counts,
                        backgroundColor: '#0056b3',
                        borderColor: '#004494',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                precision: 0
                            }}
                        }}
                    }}
                }}
            }});
        }}
        
        // Render the tags distribution chart
        function renderTagsChart() {{
            const ctx = document.createElement('canvas');
            document.getElementById('tags-chart').appendChild(ctx);
            
            const tags = Object.keys(tagCounts);
            const counts = Object.values(tagCounts);
            const bgColors = tags.map(tag => tagColors[tag] || '#f0f0f0');
            
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: tags,
                    datasets: [{{
                        data: counts,
                        backgroundColor: bgColors,
                        borderColor: 'white',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'right',
                            onClick: (e, legendItem, legend) => {{
                                filterNotesByTag(legendItem.text);
                            }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return `${{context.label}}: ${{context.raw}} notes`;
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
        
        // Set up event listeners
        function setupEventListeners() {{
            // Expand all notes
            expandAllButton.addEventListener('click', () => {{
                document.querySelectorAll('.note').forEach(note => {{
                    note.classList.add('expanded');
                }});
            }});
            
            // Collapse all notes
            collapseAllButton.addEventListener('click', () => {{
                document.querySelectorAll('.note').forEach(note => {{
                    note.classList.remove('expanded');
                }});
            }});
            
            // Sort by date
            sortByDateButton.addEventListener('click', () => {{
                const notes = Array.from(document.querySelectorAll('.note'));
                
                // Toggle sort direction
                if (currentSort === 'date-desc') {{
                    notes.sort((a, b) => {{
                        return new Date(a.getAttribute('data-date')) - new Date(b.getAttribute('data-date'));
                    }});
                    currentSort = 'date-asc';
                    sortByDateButton.textContent = 'Sort Newest First';
                }} else {{
                    notes.sort((a, b) => {{
                        return new Date(b.getAttribute('data-date')) - new Date(a.getAttribute('data-date'));
                    }});
                    currentSort = 'date-desc';
                    sortByDateButton.textContent = 'Sort Oldest First';
                }}
                
                // Reappend notes in new order
                notes.forEach(note => {{
                    notesContainer.appendChild(note);
                }});
            }});
            
            // Group by tag
            groupByTagButton.addEventListener('click', () => {{
                if (currentGroup === 'tag') {{
                    // Reset grouping
                    renderNotes();
                    currentGroup = 'none';
                    groupByTagButton.textContent = 'Group by Tag';
                    return;
                }}
                
                // Group by tag
                currentGroup = 'tag';
                groupByTagButton.textContent = 'Remove Grouping';
                
                // Clear container
                notesContainer.innerHTML = '';
                
                // Get all unique tags
                const tags = new Set();
                notesData.notes.forEach(note => {{
                    if (note.tags) {{
                        note.tags.split(',').forEach(tag => {{
                            tag = tag.trim();
                            if (tag) tags.add(tag);
                        }});
                    }}
                }});
                
                // Add uncategorized group
                tags.add('uncategorized');
                
                // Create groups for each tag
                tags.forEach(tag => {{
                    const groupDiv = document.createElement('div');
                    groupDiv.classList.add('tag-group');
                    
                    const groupHeader = document.createElement('h3');
                    groupHeader.style.backgroundColor = tagColors[tag] || '#f0f0f0';
                    groupHeader.style.padding = '10px';
                    groupHeader.style.borderRadius = '5px';
                    groupHeader.style.marginTop = '20px';
                    
                    // Count notes with this tag
                    const tagNotes = notesData.notes.filter(note => {{
                        if (tag === 'uncategorized') {{
                            return !note.tags || note.tags.trim() === '';
                        }}
                        return note.tags && note.tags.split(',').map(t => t.trim()).includes(tag);
                    }});
                    
                    groupHeader.textContent = `${{tag}} (${{tagNotes.length}})`;
                    groupDiv.appendChild(groupHeader);
                    
                    // Add notes to this group
                    tagNotes.forEach(note => {{
                        const noteDiv = document.createElement('div');
                        noteDiv.classList.add('note');
                        noteDiv.setAttribute('data-id', note.id);
                        noteDiv.setAttribute('data-date', note.created_at);
                        noteDiv.setAttribute('data-tags', note.tags || '');
                        
                        const created = new Date(note.created_at);
                        const formattedDate = created.toLocaleDateString('en-US', {{ 
                            weekday: 'short',
                            month: 'short', 
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        }});
                        
                        // Create the note header
                        const noteHeader = document.createElement('div');
                        noteHeader.classList.add('note-header');
                        
                        // Create the note title
                        const titleEl = document.createElement('h3');
                        titleEl.textContent = note.title;
                        
                        // Create tags element
                        const tagsEl = document.createElement('div');
                        tagsEl.classList.add('note-tags');
                        
                        // Add tags if any
                        if (note.tags) {{
                            note.tags.split(',').forEach(noteTag => {{
                                noteTag = noteTag.trim();
                                if (noteTag) {{
                                    const tagEl = document.createElement('span');
                                    tagEl.classList.add('tag');
                                    tagEl.textContent = noteTag;
                                    tagEl.style.backgroundColor = tagColors[noteTag] || '#f0f0f0';
                                    
                                    // Make tags clickable for filtering
                                    tagEl.addEventListener('click', (e) => {{
                                        e.stopPropagation(); // Don't toggle note expansion
                                        filterNotesByTag(noteTag);
                                    }});
                                    
                                    tagsEl.appendChild(tagEl);
                                }}
                            }});
                        }}
                        
                        // Add elements to header
                        noteHeader.appendChild(titleEl);
                        noteHeader.appendChild(tagsEl);
                        
                        // Create meta information element
                        const metaEl = document.createElement('div');
                        metaEl.classList.add('note-meta');
                        metaEl.textContent = `Created: ${{formattedDate}}`;
                        
                        // Create the content container
                        const contentEl = document.createElement('div');
                        contentEl.classList.add('note-content');
                        contentEl.classList.add('markdown-body');
                        contentEl.innerHTML = marked.parse(note.content);
                        
                        // Add everything to the note
                        noteDiv.appendChild(noteHeader);
                        noteDiv.appendChild(metaEl);
                        noteDiv.appendChild(contentEl);
                        
                        // Toggle expansion when header is clicked
                        noteHeader.addEventListener('click', () => {{
                            noteDiv.classList.toggle('expanded');
                        }});
                        
                        groupDiv.appendChild(noteDiv);
                    }});
                    
                    if (tagNotes.length > 0) {{
                        notesContainer.appendChild(groupDiv);
                    }}
                }});
            }});
        }}
        
        // Initialize the page
        init();
    </script>
</body>
</html>"""
    
    return html