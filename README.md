# GitHub Sync for Notes Database

This feature automatically syncs your notes database with GitHub each time you add a new note. The database file is committed and pushed to GitHub, creating a backup and version history of your notes.

## Setup

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

## Usage

Simply add notes normally using the `add_note.py` script:

```bash
python -m src.note_taking.add_note --title "My Note" --content "This is my note content" --tag "example"
```

The script will:
1. Add the note to the database
2. Display statistics about your notes
3. Automatically commit and push the database file to GitHub

You'll see a confirmation message when the GitHub sync is successful, or an error message if there's a problem with the synchronization.

# GitHub Sync for Notes Database

This feature automatically syncs your notes database with GitHub each time you add a new note. The database file is committed and pushed to GitHub, creating a backup and version history of your notes.

## Setup

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

## Usage

Simply add notes normally using the `add_note.py` script:

```bash
python -m src.note_taking.add_note --title "My Note" --content "This is my note content" --tag "example"
```

## How It Works

The system is designed to handle the database synchronization safely:

1. **Before adding a note**: The system checks if your local Git repository is behind the remote
   - If you're behind (e.g., changes were made on another device), you'll be prompted to run `git pull` first
   - This prevents conflicts and ensures you're always working with the latest database

2. **After adding a note**: If the repository is up to date
   - The note is added to the database
   - The database file is committed with the message "Add note: [note title]"
   - Changes are pushed to GitHub

This approach ensures data integrity by preventing you from overwriting changes made elsewhere.

## Keeping Up to Date

To manually update your local database with the latest from GitHub, simply use Git commands:

```bash
git pull
```

It's recommended to do this regularly if you use multiple devices to add notes.
