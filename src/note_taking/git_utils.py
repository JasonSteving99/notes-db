import subprocess
from pathlib import Path
from typing import Optional, List, Union


def sync_database_to_github(db_path: Path, note_title: str) -> tuple[bool, str]:
    """
    Commit and push the database file to GitHub.
    
    Args:
        db_path: Path to the database file
        note_title: Title of the added note (used in commit message)
        
    Returns:
        Tuple of (success_status, message)
    """
    repo_root = get_git_repo_root()
    if repo_root is None:
        return False, "Not in a Git repository"
    
    rel_path = get_database_rel_path(db_path)
    if rel_path is None:
        return False, "Database is outside the Git repository"
    
    # Prepare the commit message
    commit_message = f"Add note: {note_title}"
    
    try:
        # Switch to repository root for Git operations
        original_dir = os.getcwd()
        os.chdir(repo_root)
        
        try:
            # Add the database file
            subprocess.run(
                ["git", "add", str(rel_path)],
                check=True,
                capture_output=True
            )
            
            # Check if there are changes to commit
            diff_result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                capture_output=True
            )
            
            # If return code is 0, there are no changes
            if diff_result.returncode == 0:
                return False, "No changes to commit"
            
            # Commit changes
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                check=True,
                capture_output=True
            )
            
            # Push to remote
            push_result = subprocess.run(
                ["git", "push"],
                check=True,
                capture_output=True,
                text=True
            )
            
            return True, "Successfully synchronized database with GitHub"
        finally:
            # Restore original working directory
            os.chdir(original_dir)
            
    except subprocess.CalledProcessError as e:
        os.chdir(original_dir)  # Make sure we restore the directory even if an exception occurs
        return False, f"Git operation failed: {str(e)}"import os

def get_git_repo_root() -> Optional[Path]:
    """
    Find the root directory of the Git repository.
    
    Returns:
        Path to the Git repository root or None if not in a Git repository
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None


def get_database_rel_path(db_path: Path) -> Optional[Path]:
    """
    Get the relative path of the database file from the Git repository root.
    
    Args:
        db_path: Absolute path to the database file
        
    Returns:
        Relative path from Git root to database or None if not in a Git repo
    """
    repo_root = get_git_repo_root()
    if repo_root is None:
        return None
    
    try:
        return db_path.relative_to(repo_root)
    except ValueError:
        # Database is outside of the Git repository
        return None


def check_if_behind_remote() -> tuple[bool, str]:
    """
    Check if local repository is behind the remote.
    
    Returns:
        Tuple of (is_behind, message)
    """
    try:
        # Switch to repository root for Git operations
        repo_root = get_git_repo_root()
        if repo_root is None:
            return False, "Not in a Git repository"
        
        original_dir = os.getcwd()
        os.chdir(repo_root)
        
        try:
            # Fetch from remote to get latest refs
            subprocess.run(
                ["git", "fetch"],
                check=True,
                capture_output=True
            )
            
            # Check if we're behind the remote branch
            status_result = subprocess.run(
                ["git", "status", "-sb"],
                check=True,
                capture_output=True,
                text=True
            )
            
            # If we're behind the remote (contains "[behind")
            if "[behind" in status_result.stdout:
                return True, "Local repository is behind remote. Run 'git pull' before proceeding."
            
            return False, "Up to date with remote"
            
        finally:
            # Restore original working directory
            os.chdir(original_dir)
            
    except subprocess.CalledProcessError as e:
        return False, f"Git operation failed: {str(e)}"


def pull_latest_changes() -> tuple[bool, str]:
    """
    Pull the latest changes from the remote repository.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Switch to repository root for Git operations
        repo_root = get_git_repo_root()
        if repo_root is None:
            return False, "Not in a Git repository"
        
        original_dir = os.getcwd()
        os.chdir(repo_root)
        
        try:
            # Pull from remote
            subprocess.run(
                ["git", "pull"],
                check=True,
                capture_output=True
            )
            
            return True, "Successfully pulled latest changes"
            
        finally:
            # Restore original working directory
            os.chdir(original_dir)
            
    except subprocess.CalledProcessError as e:
        return False, f"Git pull failed: {str(e)}"

