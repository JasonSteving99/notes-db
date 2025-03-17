# NoteTaking: Vector-Based Notes with Claude Desktop Integration

This tool provides a vector-based note-taking system with semantic search capabilities. It's designed to be used directly with Claude Desktop as an MCP server, allowing you to manage and search your notes seamlessly from your Claude interface.

## Setting Up as Claude Desktop MCP Server

### Prerequisites

- [UV package manager](https://github.com/astral-sh/uv)
- [Claude Desktop](https://www.anthropic.com/claude) application
- A Gemini API key for embeddings generation

### Configuration

**Note about Environment Variables**: The `HOME` environment variable must be explicitly set in the configuration because Claude Desktop doesn't pass through environment variables to commands it runs. This is crucial for DuckDB to properly locate and use the vector search extension.


2. **Create Claude Desktop Configuration**

   Create or update your `claude_desktop_config.json` file with the following MCP server configuration:

   ```json
   {
     "mcpServers": {
        "note_taking": {
         "command": "uv",
         "args": [
           "run",
           "--directory",
           "/path/to/your/NoteTaking",
           "--with",
           "click-clack",
           "--",
           "click-clack",
           "--mcp",
           "--module-path",
           "/path/to/your/NoteTaking"
         ],
         "env": {
           "GEMINI_API_KEY": "your-gemini-api-key-here",
           "HOME": "/your/home/directory/"
         }
       }
     }
   }
   ```

   Replace paths and API key with your own values.

3. **Restart Claude Desktop**

   After saving your configuration, restart Claude Desktop to apply the changes.

## Usage with Claude Desktop

Once your MCP server is configured, you can interact with your note-taking system directly from Claude Desktop:

- **Adding Notes**: Ask Claude to add a note with a title, content, and optional tags
- **Searching Notes**: Request Claude to search your notes database by semantic similarity
- **Managing Notes**: View statistics and organize your notes collection

Example interactions:
- "Add a note titled 'Python Decorators' with content explaining how decorators work in Python and tag it as 'programming'"
- "Search my notes for information about vector databases"
- "Find notes related to machine learning with the tag 'AI'"

## GitHub Sync for Notes Database

This feature automatically syncs your notes database with GitHub each time you add a new note. The database file is committed and pushed to GitHub, creating a backup and version history of your notes.

### Setup

1. **Initialize Git Repository**

   If you haven't already, initialize a Git repository in your project directory:
   ```bash
   git init
   ```

2. **Add Remote Repository**

   Add your GitHub repository as a remote:
   ```bash
   git remote add origin https://github.com/yourusername/your-notes-repo.git
   ```

3. **Configure Git Authentication**

   Make sure you have configured Git authentication correctly to push to GitHub without manual credential entry:
   
   - SSH keys (recommended): https://docs.github.com/en/authentication/connecting-to-github-with-ssh
   - Personal access token: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
   - Git credential helper: https://git-scm.com/docs/gitcredentials

### How It Works

The system is designed to handle the database synchronization safely:

1. **Before adding a note**: The system checks if your local Git repository is behind the remote
   - If you're behind (e.g., changes were made on another device), you'll be prompted to run `git pull` first
   - This prevents conflicts and ensures you're always working with the latest database

2. **After adding a note**: If the repository is up to date
   - The note is added to the database
   - The database file is committed with the message "Add note: [note title]"
   - Changes are pushed to GitHub

## Core Features

- **Vector Embeddings**: Uses Gemini API to create semantic embeddings of your notes
- **Semantic Search**: Find notes based on meaning, not just keywords
- **Tag Organization**: Categorize notes with flexible tagging
- **Version Control**: Full Git integration for backup and synchronization
- **Claude Integration**: Seamless interaction through Claude Desktop

## Technical Details

- **Database**: DuckDB with vector search capabilities
- **Embeddings**: Gemini embedding model (3072 dimensions)
- **MCP Protocol**: Click-Clack for Claude Desktop integration

