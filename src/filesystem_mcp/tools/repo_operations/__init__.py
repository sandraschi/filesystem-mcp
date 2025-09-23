"""
Repository operations for the Filesystem MCP - FastMCP 2.12 compliant.

This module provides comprehensive Git repository operations using FastMCP 2.12 patterns.
All tools are registered using the @_get_app().tool() decorator pattern for maximum compatibility.
"""

import os
import shutil
import logging
import sys
import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Literal
from datetime import datetime
from enum import Enum

import git
from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict

# Configure structured logging for this module
logger = logging.getLogger(__name__)

# Import app locally in functions to avoid circular imports
def _get_app():
    """Get the app instance locally to avoid circular imports."""
    from ... import app
    return app

class CloneRepoRequest(BaseModel):
    """Request model for cloning a Git repository - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    repo_url: HttpUrl = Field(
        ...,
        description="URL of the Git repository to clone"
    )
    target_dir: Optional[str] = Field(
        None,
        description="Directory to clone into (default: current directory)"
    )
    branch: Optional[str] = Field(
        None,
        description="Branch to clone (default: default branch)"
    )
    depth: Optional[int] = Field(
        None,
        ge=1,
        description="Create a shallow clone with history truncated to this many commits"
    )
    single_branch: bool = Field(
        True,
        description="Clone only the history leading to the tip of a single branch"
    )
    no_checkout: bool = Field(
        False,
        description="Don't checkout the working directory after cloning"
    )

    @field_validator('target_dir')
    @classmethod
    def validate_target_dir(cls, v):
        if v is not None:
            try:
                path = Path(v).expanduser().absolute()
                # Check if parent directory exists and is writable
                if not path.parent.exists():
                    try:
                        path.parent.mkdir(parents=True, exist_ok=True)
                    except OSError as e:
                        raise ValueError(f"Cannot create parent directory: {e}")
                if not os.access(path.parent, os.W_OK):
                    raise ValueError(f"No write permission in directory: {path.parent}")
            except Exception as e:
                raise ValueError(f"Invalid target directory: {e}")
        return v


class RepoStatusRequest(BaseModel):
    """Request model for getting repository status - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    repo_path: str = Field(
        ".",
        description="Path to the Git repository (default: current directory)"
    )
    include_staged: bool = Field(
        True,
        description="Include information about staged changes"
    )
    include_unstaged: bool = Field(
        True,
        description="Include information about unstaged changes"
    )
    include_untracked: bool = Field(
        True,
        description="Include information about untracked files"
    )
    include_remote: bool = Field(
        False,
        description="Include information about remote repository status"
    )

    @field_validator('repo_path')
    @classmethod
    def validate_repo_path(cls, v):
        try:
            path = Path(v).expanduser().absolute()
            if not path.exists():
                raise ValueError(f"Path does not exist: {v}")
            return str(path)
        except Exception as e:
            raise ValueError(f"Invalid repository path: {e}")

@_get_app().tool()
async def clone_repo(
    repo_url: str,
    target_dir: Optional[str] = None,
    branch: Optional[str] = None,
    depth: Optional[int] = None,
    single_branch: bool = True,
    no_checkout: bool = False
) -> dict:
    """Clone a Git repository with advanced options and comprehensive error handling.

    This tool clones a Git repository with support for shallow cloning,
    single branch cloning, and other advanced Git options. It provides
    detailed status information about the cloned repository with proper
    error handling and structured logging for debugging.

    Args:
        repo_url: URL of the Git repository to clone
        target_dir: Directory to clone into (default: current directory)
        branch: Branch to clone (default: default branch)
        depth: Create a shallow clone with history truncated to this many commits
        single_branch: Clone only the history leading to a single branch (default: True)
        no_checkout: Clone without checking out any branch (default: False)

    Returns:
        Dictionary containing clone operation results and repository information

    Error Handling:
        Returns error information if clone fails, directory access denied, or other issues
    """
    try:
        logger.info(f"Cloning repository from {repo_url} to {target_dir}")

        # Determine target directory
        if target_dir is None:
            # Default to a directory named after the repo in the current directory
            repo_name = str(repo_url).split('/')[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            target_dir = str(Path.cwd() / repo_name)

        # Resolve and validate target path
        target_path = Path(target_dir).expanduser().absolute()

        # Check if target directory exists and is empty
        if target_path.exists():
            if any(target_path.iterdir()):
                logger.error(f"Target directory is not empty: {target_dir}")
                return {
                    "success": False,
                    "error": f"Target directory is not empty: {target_dir}",
                    "repo_url": repo_url
                }
        else:
            # Ensure parent directory exists and is writable
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if not os.access(target_path.parent, os.W_OK):
                logger.error(f"No write permission in directory: {target_path.parent}")
                return {
                    "success": False,
                    "error": f"No write permission in directory: {target_path.parent}",
                    "repo_url": repo_url
                }

        # Prepare clone options
        clone_kwargs = {
            'single_branch': single_branch,
            'no_checkout': no_checkout
        }

        if branch:
            clone_kwargs['branch'] = branch
        if depth:
            clone_kwargs['depth'] = depth

        # Perform the clone
        try:
            repo = git.Repo.clone_from(
                str(repo_url),
                str(target_path),
                **clone_kwargs
            )
        except git.exc.GitCommandError as e:
            logger.error(f"Git command error while cloning repository: {e}")
            return {
                "success": False,
                "error": f"Failed to clone repository: {str(e)}",
                "repo_url": repo_url,
                "target_dir": target_dir
            }

        # Get repository information
        head_info = {}
        if repo.head.is_valid():
            head_info = {
                'branch': str(repo.active_branch) if not repo.head.is_detached else None,
                'commit': repo.head.commit.hexsha,
                'commit_message': repo.head.commit.message.strip(),
                'commit_author': str(repo.head.commit.author),
                'commit_date': repo.head.commit.committed_datetime.isoformat(),
                'is_detached': repo.head.is_detached
            }

        # Prepare response
        response = {
            'success': True,
            'message': f'Successfully cloned {repo_url} to {target_dir}',
            'repo_path': str(target_path),
            'git_dir': str(Path(repo.git_dir).relative_to(target_path) if repo.git_dir else None),
            'is_bare': repo.bare,
            'head': head_info,
            'remotes': [{
                'name': remote.name,
                'url': list(remote.urls)[0] if remote.urls else None
            } for remote in repo.remotes]
        }

        logger.info(f"Successfully cloned repository to {target_dir}")
        return response

    except Exception as e:
        logger.error(f"Unexpected error while cloning repository: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}",
            "repo_url": repo_url
        }

class CommitInfo(BaseModel):
    """Model for commit information."""
    hexsha: str = Field(..., description="Commit hash")
    message: str = Field(..., description="Full commit message")
    summary: str = Field(..., description="First line of commit message")
    author: str = Field(..., description="Author name and email")
    authored_date: str = Field(..., description="ISO formatted authored date")
    committed_date: str = Field(..., description="ISO formatted commit date")
    parents: List[str] = Field(..., description="List of parent commit hashes")


class ChangeInfo(BaseModel):
    """Model for file change information."""
    change_type: str = Field(..., description="Type of change (A=added, D=deleted, R=renamed, M=modified, U=unmerged)")
    a_path: Optional[str] = Field(None, description="Original path (for renames)")
    b_path: Optional[str] = Field(None, description="New path")
    new_file: bool = Field(False, description="Whether this is a new file")
    deleted_file: bool = Field(False, description="Whether this file was deleted")
    renamed: bool = Field(False, description="Whether this file was renamed")
    raw_rename_from: Optional[str] = Field(None, description="Raw rename from path")
    raw_rename_to: Optional[str] = Field(None, description="Raw rename to path")


class RepoStatusResponse(BaseModel):
    """Response model for repository status."""
    status: str = Field(..., description="Status of the operation")
    repo_path: str = Field(..., description="Path to the repository")
    is_dirty: bool = Field(..., description="Whether the working directory has uncommitted changes")
    active_branch: Optional[str] = Field(None, description="Name of the active branch")
    head_commit: Optional[CommitInfo] = Field(None, description="Information about the HEAD commit")
    staged_changes: List[Dict[str, Any]] = Field(default_factory=list, description="List of staged changes")
    unstaged_changes: List[Dict[str, Any]] = Field(default_factory=list, description="List of unstaged changes")
    untracked_files: List[str] = Field(default_factory=list, description="List of untracked files")
    remote_status: Optional[Dict[str, Any]] = Field(None, description="Status of remote tracking branches")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error message if status is 'error'")


class CommitChangesRequest(BaseModel):
    """Request model for committing changes to a Git repository - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    repo_path: str = Field(
        ".",
        description="Path to the Git repository (default: current directory)"
    )
    message: str = Field(
        ...,
        description="Commit message (required)",
        min_length=1
    )
    add_all: bool = Field(
        False,
        description="Whether to stage all changes before committing (default: False)"
    )
    paths: List[str] = Field(
        default_factory=list,
        description="Specific paths to stage before committing (default: [])"
    )
    allow_empty: bool = Field(
        False,
        description="Allow creating a commit with no changes (default: False)"
    )
    skip_hooks: bool = Field(
        False,
        description="Skip git commit hooks (default: False)"
    )

    @field_validator('repo_path')
    @classmethod
    def validate_repo_path(cls, v):
        try:
            path = Path(v).expanduser().absolute()
            if not path.exists():
                raise ValueError(f"Path does not exist: {v}")
            return str(path)
        except Exception as e:
            raise ValueError(f"Invalid repository path: {e}")


class CommitResponse(BaseModel):
    """Response model for commit operations."""
    status: str = Field(..., description="Status of the operation")
    commit_hash: Optional[str] = Field(None, description="Hash of the created commit")
    repo_path: str = Field(..., description="Path to the repository")
    branch: Optional[str] = Field(None, description="Name of the active branch")
    message: Optional[str] = Field(None, description="Commit message")
    files_changed: List[str] = Field(
        default_factory=list,
        description="List of files included in the commit"
    )
    stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Statistics about the commit (insertions, deletions, etc.)"
    )
    error: Optional[str] = Field(None, description="Error message if status is 'error'")


class RepoItemType(str, Enum):
    """Type of repository item."""
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    SUBMODULE = "submodule"
    OTHER = "other"


class RepoItem(BaseModel):
    """Model for a repository item (file or directory) - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: str = Field(..., description="Relative path from repository root")
    name: str = Field(..., description="Name of the item")
    type: RepoItemType = Field(..., description="Type of the item")
    size: Optional[int] = Field(None, description="Size in bytes (for files)")
    mime_type: Optional[str] = Field(None, description="MIME type (for files)")
    content: Optional[str] = Field(None, description="File content (if requested and applicable)")
    encoding: Optional[str] = Field(None, description="Content encoding (if content is provided)")
    children: List['RepoItem'] = Field(
        default_factory=list,
        description="Child items (for directories)"
    )
    modified: Optional[float] = Field(None, description="Last modification timestamp")
    mode: Optional[int] = Field(None, description="File mode/permissions")


class ReadRepoRequest(BaseModel):
    """Request model for reading repository contents - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    repo_path: str = Field(
        ".",
        description="Path to the Git repository (default: current directory)"
    )
    path: str = Field(
        ".",
        description="Path within the repository to read from (default: root)"
    )
    max_depth: int = Field(
        3,
        ge=1,
        le=10,
        description="Maximum depth to traverse (default: 3, max: 10)"
    )
    include_content: bool = Field(
        False,
        description="Whether to include file contents (default: False)"
    )
    max_file_size: int = Field(
        1024 * 1024,  # 1MB
        ge=0,
        description="Maximum file size to include content for in bytes (default: 1MB)"
    )
    include_hidden: bool = Field(
        False,
        description="Whether to include hidden files/directories (default: False)"
    )
    file_pattern: Optional[str] = Field(
        None,
        description="Pattern to filter files by (e.g., '*.py' for Python files)"
    )

    @field_validator('repo_path')
    @classmethod
    def validate_repo_path(cls, v):
        try:
            path = Path(v).expanduser().absolute()
            if not path.exists():
                raise ValueError(f"Path does not exist: {v}")
            return str(path)
        except Exception as e:
            raise ValueError(f"Invalid repository path: {e}")


class RepoContentResponse(BaseModel):
    """Response model for repository content."""
    status: str = Field(..., description="Status of the operation")
    repo_path: str = Field(..., description="Path to the repository")
    path: str = Field(..., description="Path that was read")
    items: List[RepoItem] = Field(
        default_factory=list,
        description="List of items in the specified path"
    )
    total_items: int = Field(
        0,
        description="Total number of items (including those not returned due to pagination)"
    )
    error: Optional[str] = Field(None, description="Error message if status is 'error'")


class BranchInfo(BaseModel):
    """Information about a Git branch."""
    name: str = Field(..., description="Name of the branch")
    is_current: bool = Field(..., description="Whether this is the currently checked out branch")
    is_remote: bool = Field(..., description="Whether this is a remote-tracking branch")
    commit_hash: str = Field(..., description="Commit hash at the tip of the branch")
    commit_message: Optional[str] = Field(None, description="Commit message")
    commit_author: Optional[str] = Field(None, description="Author of the last commit")
    commit_date: Optional[datetime] = Field(None, description="Date of the last commit")
    tracking_branch: Optional[str] = Field(None, description="Name of the tracking branch, if any")
    behind: Optional[int] = Field(None, description="Number of commits behind the tracking branch")
    ahead: Optional[int] = Field(None, description="Number of commits ahead of the tracking branch")


class ListBranchesRequest(BaseModel):
    """Request model for listing Git branches - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    repo_path: str = Field(
        ".",
        description="Path to the Git repository (default: current directory)"
    )
    list_all: bool = Field(
        False,
        description="Whether to list both remote-tracking and local branches (default: local only)"
    )
    include_commit_info: bool = Field(
        True,
        description="Whether to include commit information (default: True)"
    )
    include_remote_status: bool = Field(
        True,
        description="Whether to include remote tracking status (default: True)"
    )

    @field_validator('repo_path')
    @classmethod
    def validate_repo_path(cls, v):
        try:
            path = Path(v).expanduser().absolute()
            if not path.exists():
                raise ValueError(f"Path does not exist: {v}")
            return str(path)
        except Exception as e:
            raise ValueError(f"Invalid repository path: {e}")


class ListBranchesResponse(BaseModel):
    """Response model for listing Git branches."""
    status: str = Field(..., description="Status of the operation")
    repo_path: str = Field(..., description="Path to the repository")
    current_branch: Optional[str] = Field(None, description="Name of the current branch")
    branches: List[BranchInfo] = Field(
        default_factory=list,
        description="List of branch information"
    )
    error: Optional[str] = Field(None, description="Error message if status is 'error'")


@_get_app().tool()
async def get_repo_status(
    repo_path: str = ".",
    include_staged: bool = True,
    include_unstaged: bool = True,
    include_untracked: bool = True,
    include_remote: bool = False
) -> dict:
    """Get detailed status of a Git repository with comprehensive information.

    This tool provides comprehensive information about the current state of a
    Git repository, including staged and unstaged changes, untracked files, and
    remote synchronization status. It includes proper error handling and
    structured logging for debugging and monitoring.

    Args:
        repo_path: Path to the Git repository (default: current directory)
        include_staged: Include information about staged changes (default: True)
        include_unstaged: Include information about unstaged changes (default: True)
        include_untracked: Include information about untracked files (default: True)
        include_remote: Include information about remote repository status (default: False)

    Returns:
        Dictionary containing comprehensive repository status information

    Error Handling:
        Returns error information if repository access fails or Git commands fail
    """
    try:
        logger.info(f"Getting repository status for: {repo_path}")

        # Resolve repository path
        repo_path_obj = Path(repo_path).expanduser().absolute()

        # Check if path exists and is a valid repository
        if not repo_path_obj.exists():
            logger.warning(f"Repository path does not exist: {repo_path}")
            return {
                "success": False,
                "error": f"Repository path does not exist: {repo_path}",
                "repo_path": repo_path
            }
        
        try:
            # Open the repository
            repo = git.Repo(repo_path_obj, search_parent_directories=True)

            # Initialize response data
            active_branch = None
            head_commit = None
            is_dirty = False

            # Get branch info
            try:
                active_branch = str(repo.active_branch)
                is_dirty = repo.is_dirty()
            except (TypeError, ValueError):
                active_branch = None  # Detached HEAD
                is_dirty = repo.is_dirty()

            # Get commit info if HEAD exists
            if not repo.bare and repo.head.is_valid():
                commit = repo.head.commit
                head_commit = {
                    "hexsha": commit.hexsha,
                    "message": commit.message.strip(),
                    "summary": commit.summary,
                    "author": f"{commit.author.name} <{commit.author.email}>" if commit.author else "Unknown",
                    "authored_date": datetime.fromtimestamp(commit.authored_date).isoformat(),
                    "committed_date": datetime.fromtimestamp(commit.committed_date).isoformat(),
                    "parents": [p.hexsha for p in commit.parents]
                }

            # Get status
            staged_changes = []
            unstaged_changes = []
            untracked_files = []

            if include_staged:
                staged_changes = [
                    {
                        'change_type': item.change_type,
                        'a_path': item.a_path,
                        'b_path': item.b_path,
                        'new_file': item.new_file,
                        'deleted_file': item.deleted_file,
                        'renamed': item.renamed,
                        'raw_rename_from': item.raw_rename_from,
                        'raw_rename_to': item.raw_rename_to
                    }
                    for item in repo.index.diff('HEAD')  # Staged changes
                ]

            if include_unstaged:
                unstaged_changes = [
                    {
                        'change_type': item.change_type,
                        'a_path': item.a_path,
                        'b_path': item.b_path,
                        'new_file': item.new_file,
                        'deleted_file': item.deleted_file,
                        'renamed': item.renamed,
                        'raw_rename_from': item.raw_rename_from,
                        'raw_rename_to': item.raw_rename_to
                    }
                    for item in repo.index.diff(None)  # Unstaged changes
                ]

            if include_untracked:
                untracked_files = [str(p) for p in repo.untracked_files]
            
            # Get remote status if requested
            remote_status = {}
            if include_remote and repo.remotes:
                for remote in repo.remotes:
                    try:
                        remote_status[remote.name] = {
                            'url': next(iter(remote.urls), None),
                            'fetch_info': [
                                {
                                    'commit': ref.commit.hexsha,
                                    'name': ref.name,
                                    'is_remote': ref.is_remote(),
                                    'is_valid': ref.is_valid()
                                }
                                for ref in remote.refs
                            ]
                        }
                    except Exception as e:
                        logger.warning(f"Could not get status for remote {remote.name}: {e}")
                        remote_status[remote.name] = {
                            'error': str(e),
                            'url': next(iter(remote.urls), None)
                        }

            # Build the response
            response = {
                "success": True,
                "repo_path": str(repo_path_obj),
                "is_dirty": is_dirty,
                "active_branch": active_branch,
                "head_commit": head_commit,
                "staged_changes": staged_changes,
                "unstaged_changes": unstaged_changes,
                "untracked_files": untracked_files,
                "remote_status": remote_status if include_remote else None,
                "message": "Repository status retrieved successfully"
            }

            logger.info(f"Successfully retrieved status for repository: {repo_path_obj}")
            return response

        except git.InvalidGitRepositoryError as e:
            logger.error(f"Not a valid Git repository: {repo_path_obj}")
            return {
                "success": False,
                "error": f"Not a valid Git repository: {repo_path_obj}",
                "repo_path": repo_path
            }
        except git.NoSuchPathError as e:
            logger.error(f"Repository not found: {repo_path_obj}")
            return {
                "success": False,
                "error": f"Repository not found: {repo_path_obj}",
                "repo_path": repo_path
            }
        except git.GitCommandError as e:
            logger.error(f"Git command failed: {e}")
            return {
                "success": False,
                "error": f"Git command failed: {str(e)}",
                "repo_path": repo_path
            }

    except Exception as e:
        logger.error(f"Unexpected error getting repository status for {repo_path}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to get repository status: {str(e)}",
            "repo_path": repo_path
        }

@_get_app().tool()
async def list_branches(
    request: ListBranchesRequest
) -> ListBranchesResponse:
    """
    List Git branches with detailed information and tracking status.
    
    This function provides comprehensive information about Git branches, including
    commit information and remote tracking status.
    
    Args:
        request: ListBranchesRequest object containing:
            - repo_path: Path to the Git repository (default: current directory)
            - list_all: Whether to list both remote-tracking and local branches
            - include_commit_info: Whether to include commit information
            - include_remote_status: Whether to include remote tracking status
    
    Returns:
        ListBranchesResponse: Detailed information about branches.
        
    Returns:
        ListBranchesResponse with error details if repository access fails.
    """
    try:
        # Initialize response
        response = ListBranchesResponse(
            status="success",
            repo_path=request.repo_path,
            branches=[]
        )
        
        # Open the repository
        try:
            repo = git.Repo(request.repo_path, search_parent_directories=True)
            response.current_branch = str(repo.active_branch) if not repo.head.is_detached else None
        except git.InvalidGitRepositoryError:
            logger.warning(f"Not a valid Git repository: {request.repo_path}")
            return ListBranchesResponse(
                status="error",
                repo_path=request.repo_path,
                error=f"Not a valid Git repository: {request.repo_path}"
            )
        
        # Get the current branch if not in detached HEAD state
        current_branch = None
        if not repo.head.is_detached:
            current_branch = str(repo.active_branch)
        
        # Track which remote branches we've seen to avoid duplicates
        seen_remote_branches = set()
        
        # Process local branches
        for ref in repo.heads:
            branch_info = _get_branch_info(
                repo=repo,
                ref=ref,
                is_remote=False,
                is_current=ref.name == current_branch if current_branch else False,
                include_commit_info=request.include_commit_info,
                include_remote_status=request.include_remote_status
            )
            response.branches.append(branch_info)
        
        # Process remote branches if requested
        if request.list_all:
            for remote in repo.remotes:
                for ref in remote.refs:
                    # Skip HEAD refs and already seen branches
                    if ref.name.endswith('/HEAD') or ref.name in seen_remote_branches:
                        continue
                    
                    # Add to seen set
                    seen_remote_branches.add(ref.name)
                    
                    # Skip if we already have this as a local branch
                    local_branch_name = ref.name.split('/')[-1]
                    if any(b.name == local_branch_name for b in repo.heads):
                        continue
                    
                    branch_info = _get_branch_info(
                        repo=repo,
                        ref=ref,
                        is_remote=True,
                        is_current=False,
                        include_commit_info=request.include_commit_info,
                        include_remote_status=request.include_remote_status
                    )
                    response.branches.append(branch_info)
        
        # Sort branches: current branch first, then local branches, then remote branches
        response.branches.sort(
            key=lambda x: (
                not x.is_current,  # Current branch first
                x.is_remote,      # Local before remote
                x.name.lower()    # Alphabetical within each group
            )
        )
        
        logger.info(f"Listed {len(response.branches)} branches from repository: {request.repo_path}")
        return response

    except Exception as e:
        error_msg = f"Unexpected error while listing branches: {str(e)}"
        logger.exception(error_msg)
        return ListBranchesResponse(
            status="error",
            repo_path=request.repo_path,
            error=error_msg
        )


def _get_branch_info(
    repo: git.Repo,
    ref: Union[git.Head, git.RemoteReference],
    is_remote: bool,
    is_current: bool,
    include_commit_info: bool = True,
    include_remote_status: bool = True
) -> BranchInfo:
    """
    Get detailed information about a Git branch.
    
    Args:
        repo: The Git repository object.
        ref: The branch reference.
        is_remote: Whether this is a remote branch.
        is_current: Whether this is the current branch.
        include_commit_info: Whether to include commit information.
        include_remote_status: Whether to include remote tracking status.
        
    Returns:
        BranchInfo: Detailed information about the branch.
    """
    branch_name = ref.name.split('/')[-1] if is_remote else ref.name
    
    # Get commit information if requested
    commit_message = None
    commit_author = None
    commit_date = None
    
    if include_commit_info and ref.commit:
        commit = ref.commit
        commit_message = commit.message.strip() if commit.message else None
        if commit.author:
            commit_author = f"{commit.author.name} <{commit.author.email}>"
        if hasattr(commit, 'committed_date'):
            commit_date = datetime.fromtimestamp(commit.committed_date)
    
    # Get tracking information if this is a local branch and tracking is enabled
    tracking_branch = None
    behind = None
    ahead = None
    
    if include_remote_status and not is_remote and hasattr(ref, 'tracking_branch') and ref.tracking_branch():
        tracking_branch = ref.tracking_branch().name
        
        # Calculate commits ahead/behind
        try:
            # Get the common ancestor
            base = repo.merge_base(ref, ref.tracking_branch())
            if base:
                # Get commits that are in local but not in remote
                ahead = sum(1 for _ in repo.iter_commits(f"{base[0].hexsha}..{ref.commit.hexsha}"))
                # Get commits that are in remote but not in local
                behind = sum(1 for _ in repo.iter_commits(f"{ref.commit.hexsha}..{ref.tracking_branch().commit.hexsha}"))
        except Exception as e:
            logger.warning(f"Could not calculate ahead/behind for {ref.name}: {str(e)}")
    
    return BranchInfo(
        name=branch_name,
        is_current=is_current,
        is_remote=is_remote,
        commit_hash=ref.commit.hexsha if ref.commit else "",
        commit_message=commit_message,
        commit_author=commit_author,
        commit_date=commit_date,
        tracking_branch=tracking_branch,
        ahead=ahead,
        behind=behind
    )


@_get_app().tool()
async def commit_changes(
    request: CommitChangesRequest
) -> CommitResponse:
    """
    Commit changes to a Git repository with detailed options.
    
    This function stages and commits changes in a Git repository with support for
    partial staging, commit hooks, and detailed commit information.
    
    Args:
        request: CommitChangesRequest object containing:
            - repo_path: Path to the Git repository (default: current directory)
            - message: Commit message (required)
            - add_all: Whether to stage all changes before committing
            - paths: Specific paths to stage before committing
            - allow_empty: Allow creating a commit with no changes
            - skip_hooks: Skip git commit hooks
    
    Returns:
        CommitResponse: Detailed information about the created commit.
        
    Returns:
        CommitResponse with error details if commit operation fails.
    """
    try:
        # Initialize response
        response = CommitResponse(
            status="success",
            repo_path=request.repo_path,
            message=request.message
        )
        
        # Open the repository
        try:
            repo = git.Repo(request.repo_path, search_parent_directories=True)
            response.branch = str(repo.active_branch) if not repo.head.is_detached else None
        except git.InvalidGitRepositoryError:
            logger.warning(f"Not a valid Git repository: {request.repo_path}")
            return CommitResponse(
                status="error",
                repo_path=request.repo_path,
                error=f"Not a valid Git repository: {request.repo_path}"
            )
        
        # Stage changes if needed
        staged_files = []
        if request.add_all:
            # Stage all changes including untracked files
            repo.git.add(all=True)
            # Get list of staged files
            staged_files = [item.a_path for item in repo.index.diff('HEAD')] + repo.untracked_files
        elif request.paths:
            # Stage specific paths
            for path in request.paths:
                repo.git.add(path)
            # Get list of actually staged files (in case some paths were invalid)
            staged_files = [item.a_path for item in repo.index.diff('HEAD')]
        
        # Check if there are any changes to commit
        if not request.allow_empty and not repo.index.diff('HEAD') and not repo.untracked_files:
            response.status = "no_changes"
            response.message = "No changes to commit"
            return response
        
        # Prepare commit command
        commit_kwargs = {
            'message': request.message,
            'skip_hooks': request.skip_hooks
        }
        
        try:
            # Perform the commit
            commit = repo.index.commit(**commit_kwargs)
            response.commit_hash = commit.hexsha
            response.message = commit.message.strip()
            
            # Get detailed information about the commit
            if commit.parents:
                # Compare with parent commit to get changed files
                diff_index = commit.parents[0].diff(commit)
                response.files_changed = [d.a_path for d in diff_index]
                
                # Calculate basic stats
                insertions = 0
                deletions = 0
                files = 0
                
                for diff in diff_index:
                    if diff.new_file or diff.deleted_file or diff.renamed:
                        files += 1
                        insertions += diff.diff.count('\n+') - 1  # Subtract 1 for the diff header
                        deletions += diff.diff.count('\n-') - 1  # Subtract 1 for the diff header
                
                response.stats = {
                    'insertions': max(0, insertions),
                    'deletions': max(0, deletions),
                    'files': files
                }
            
            logger.info(f"Committed {len(response.files_changed)} files to repository: {request.repo_path}")
            return response
            
        except git.GitCommandError as e:
            error_msg = f"Failed to create commit: {str(e)}"
            logger.error(error_msg)
            return CommitResponse(
                status="error",
                repo_path=request.repo_path,
                error=error_msg
            )

    except Exception as e:
        error_msg = f"Unexpected error while committing changes: {str(e)}"
        logger.exception(error_msg)
        return CommitResponse(
            status="error",
            repo_path=request.repo_path,
            error=error_msg
        )

@_get_app().tool()
async def read_repo(
    request: ReadRepoRequest
) -> RepoContentResponse:
    """
    Read and explore repository contents with detailed options.
    
    This function provides a structured view of a Git repository's contents,
    with support for filtering, content inclusion, and depth control.
    
    Args:
        request: ReadRepoRequest object containing:
            - repo_path: Path to the Git repository (default: current directory)
            - path: Path within the repository to read from (default: root)
            - max_depth: Maximum depth to traverse (default: 3, max: 10)
            - include_content: Whether to include file contents (default: False)
            - max_file_size: Maximum file size to include content for (default: 1MB)
            - include_hidden: Whether to include hidden files/directories (default: False)
            - file_pattern: Pattern to filter files by (e.g., '*.py' for Python files)
    
    Returns:
        RepoContentResponse: Structured repository contents.
        
    Returns:
        RepoContentResponse with error details if repository access fails.
    """
    try:
        # Initialize response
        response = RepoContentResponse(
            status="success",
            repo_path=request.repo_path,
            path=request.path,
            items=[]
        )
        
        # Open the repository
        try:
            repo = git.Repo(request.repo_path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            logger.warning(f"Not a valid Git repository: {request.repo_path}")
            return RepoContentResponse(
                status="error",
                repo_path=request.repo_path,
                path=request.path,
                error=f"Not a valid Git repository: {request.repo_path}"
            )
        
        # Normalize path and ensure it's relative to the repo root
        repo_root = Path(repo.working_tree_dir)
        rel_path = Path(request.path).as_posix().lstrip('/')
        
        # Get the tree for the requested path
        try:
            if rel_path == '.':
                tree = repo.tree()
            else:
                tree = repo.tree()
                for part in rel_path.split('/'):
                    if not part:
                        continue
                    try:
                        tree = tree[part]
                    except KeyError:
                        logger.warning(f"Path not found in repository: {rel_path}")
                        return RepoContentResponse(
                            status="error",
                            repo_path=request.repo_path,
                            path=request.path,
                            error=f"Path not found in repository: {rel_path}"
                        )
        except Exception as e:
            error_msg = f"Error accessing repository path {rel_path}: {str(e)}"
            logger.error(error_msg)
            return RepoContentResponse(
                status="error",
                repo_path=request.repo_path,
                path=request.path,
                error=error_msg
            )
        
        # Process each item in the current tree
        for item in tree:
            # Skip hidden files/directories if not requested
            if not request.include_hidden and item.name.startswith('.'):
                continue
                
            # Filter by file pattern if specified
            if request.file_pattern and not fnmatch.fnmatch(item.name, request.file_pattern):
                continue
            
            # Determine item type
            if item.type == 'tree':
                item_type = RepoItemType.DIRECTORY
            elif item.type == 'blob':
                item_type = RepoItemType.FILE
            elif item.type == 'commit':  # Submodule
                item_type = RepoItemType.SUBMODULE
            elif item.mode == 0o120000:  # Symlink
                item_type = RepoItemType.SYMLINK
            else:
                item_type = RepoItemType.OTHER
            
            # Create the base item
            item_path = str(Path(rel_path) / item.name) if rel_path != '.' else item.name
            
            repo_item = RepoItem(
                path=item_path,
                name=item.name,
                type=item_type,
                size=item.size if hasattr(item, 'size') else None,
                modified=item.committed_date if hasattr(item, 'committed_date') else None,
                mode=item.mode if hasattr(item, 'mode') else None
            )
            
            # Handle file content if requested
            if item_type == RepoItemType.FILE and request.include_content and item.size <= request.max_file_size:
                try:
                    # Get the blob content
                    blob = repo.git.show(f"HEAD:{item_path}")
                    repo_item.content = blob
                    repo_item.encoding = 'utf-8'
                except Exception as e:
                    logger.warning(f"Could not read content of {item_path}: {str(e)}")
            
            # For directories, add a placeholder for children
            if item_type == RepoItemType.DIRECTORY and request.max_depth > 1:
                # Don't process children if we've reached max depth
                pass
            
            response.items.append(repo_item)
        
        # Sort items: directories first, then files, then by name
        response.items.sort(key=lambda x: (x.type != RepoItemType.DIRECTORY, x.name.lower()))
        response.total_items = len(response.items)
        
        logger.info(f"Read {len(response.items)} items from repository: {request.repo_path}")
        return response

    except Exception as e:
        error_msg = f"Unexpected error while reading repository: {str(e)}"
        logger.exception(error_msg)
        return RepoContentResponse(
            status="error",
            repo_path=request.repo_path,
            path=request.path,
            error=error_msg
        )
