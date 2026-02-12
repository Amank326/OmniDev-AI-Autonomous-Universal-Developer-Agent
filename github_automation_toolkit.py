"""
GitHub CLI Automation Toolkit
Comprehensive automation for GitHub operations including repos, issues, PRs,
workflows, releases, and project management without requiring elevated permissions.
"""

import os
import sys
import json
import subprocess
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import hashlib


# ===================== ENUMS =====================

class IssueState(str, Enum):
    """Issue states."""
    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


class PullRequestState(str, Enum):
    """Pull request states."""
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    ALL = "all"


class WorkflowStatus(str, Enum):
    """Workflow run status."""
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ALL = "all"


class WorkflowConclusion(str, Enum):
    """Workflow run conclusion."""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    ALL = "all"


# ===================== DATACLASSES =====================

@dataclass
class GitHubUser:
    """GitHub user information."""
    login: str
    id: int
    avatar_url: str
    profile_url: str
    name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    followers: int = 0
    following: int = 0
    public_repos: int = 0
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'login': self.login,
            'id': self.id,
            'avatar_url': self.avatar_url,
            'profile_url': self.profile_url,
            'name': self.name,
            'bio': self.bio,
            'company': self.company,
            'location': self.location,
            'followers': self.followers,
            'following': self.following,
            'public_repos': self.public_repos,
            'created_at': self.created_at
        }


@dataclass
class Repository:
    """GitHub repository information."""
    owner: str
    name: str
    url: str
    description: str
    language: Optional[str]
    stars: int
    forks: int
    watchers: int
    open_issues: int
    visibility: str
    created_at: str
    updated_at: str
    pushed_at: str
    is_private: bool
    is_fork: bool
    main_branch: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'owner': self.owner,
            'name': self.name,
            'url': self.url,
            'description': self.description,
            'language': self.language,
            'stars': self.stars,
            'forks': self.forks,
            'watchers': self.watchers,
            'open_issues': self.open_issues,
            'visibility': self.visibility,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'pushed_at': self.pushed_at,
            'is_private': self.is_private,
            'is_fork': self.is_fork,
            'main_branch': self.main_branch
        }


@dataclass
class Issue:
    """GitHub issue."""
    number: int
    title: str
    body: str
    state: str
    user: str
    assignees: List[str]
    labels: List[str]
    milestone: Optional[str]
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    url: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'number': self.number,
            'title': self.title,
            'body': self.body,
            'state': self.state,
            'user': self.user,
            'assignees': self.assignees,
            'labels': self.labels,
            'milestone': self.milestone,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'closed_at': self.closed_at,
            'url': self.url
        }


@dataclass
class PullRequest:
    """GitHub pull request."""
    number: int
    title: str
    body: str
    state: str
    user: str
    assignees: List[str]
    reviewers: List[str]
    labels: List[str]
    created_at: str
    updated_at: str
    merged_at: Optional[str]
    head_branch: str
    base_branch: str
    additions: int
    deletions: int
    changed_files: int
    commits: int
    url: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'number': self.number,
            'title': self.title,
            'body': self.body,
            'state': self.state,
            'user': self.user,
            'assignees': self.assignees,
            'reviewers': self.reviewers,
            'labels': self.labels,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'merged_at': self.merged_at,
            'head_branch': self.head_branch,
            'base_branch': self.base_branch,
            'additions': self.additions,
            'deletions': self.deletions,
            'changed_files': self.changed_files,
            'commits': self.commits,
            'url': self.url
        }


@dataclass
class WorkflowRun:
    """GitHub workflow run."""
    id: int
    name: str
    status: str
    conclusion: Optional[str]
    workflow_id: int
    head_branch: str
    head_sha: str
    event: str
    created_at: str
    updated_at: str
    run_number: int
    url: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'conclusion': self.conclusion,
            'workflow_id': self.workflow_id,
            'head_branch': self.head_branch,
            'head_sha': self.head_sha,
            'event': self.event,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'run_number': self.run_number,
            'url': self.url
        }


@dataclass
class Release:
    """GitHub release."""
    tag_name: str
    name: str
    body: str
    author: str
    created_at: str
    published_at: str
    draft: bool
    prerelease: bool
    asset_count: int
    download_url: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'tag_name': self.tag_name,
            'name': self.name,
            'body': self.body,
            'author': self.author,
            'created_at': self.created_at,
            'published_at': self.published_at,
            'draft': self.draft,
            'prerelease': self.prerelease,
            'asset_count': self.asset_count,
            'download_url': self.download_url
        }


# ===================== GITHUB AUTOMATION SERVICE =====================

class GitHubAutomationService:
    """GitHub automation service with comprehensive CLI operations."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub automation service."""
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.api_url = "https://api.github.com"
        self.current_user: Optional[GitHubUser] = None
        self.repositories: Dict[str, Repository] = {}
        self.issues: Dict[str, List[Issue]] = {}
        self.pull_requests: Dict[str, List[PullRequest]] = {}
        self.workflow_runs: Dict[str, List[WorkflowRun]] = {}
        self.releases: Dict[str, List[Release]] = {}
    
    def _run_command(self, cmd: str) -> Tuple[int, str, str]:
        """Run shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timeout"
        except Exception as e:
            return 1, "", str(e)
    
    def authenticate(self) -> bool:
        """Authenticate with GitHub."""
        if not self.token:
            return False
        
        cmd = f'curl -H "Authorization: token {self.token}" -s {self.api_url}/user'
        code, stdout, stderr = self._run_command(cmd)
        
        if code == 0:
            try:
                data = json.loads(stdout)
                self.current_user = GitHubUser(
                    login=data.get('login'),
                    id=data.get('id'),
                    avatar_url=data.get('avatar_url'),
                    profile_url=data.get('html_url'),
                    name=data.get('name'),
                    bio=data.get('bio'),
                    company=data.get('company'),
                    location=data.get('location'),
                    followers=data.get('followers', 0),
                    following=data.get('following', 0),
                    public_repos=data.get('public_repos', 0),
                    created_at=data.get('created_at')
                )
                return True
            except:
                return False
        return False
    
    def get_current_user(self) -> Optional[GitHubUser]:
        """Get current authenticated user."""
        return self.current_user
    
    def list_repositories(self, limit: int = 30) -> List[Repository]:
        """List user's repositories."""
        if not self.token:
            return []
        
        cmd = f'curl -H "Authorization: token {self.token}" -s "{self.api_url}/user/repos?per_page={limit}&sort=updated"'
        code, stdout, stderr = self._run_command(cmd)
        
        if code == 0:
            try:
                repos = []
                data = json.loads(stdout)
                for item in data:
                    repo = Repository(
                        owner=item['owner']['login'],
                        name=item['name'],
                        url=item['html_url'],
                        description=item.get('description', ''),
                        language=item.get('language'),
                        stars=item.get('stargazers_count', 0),
                        forks=item.get('forks_count', 0),
                        watchers=item.get('watchers_count', 0),
                        open_issues=item.get('open_issues_count', 0),
                        visibility=item.get('visibility', 'public'),
                        created_at=item.get('created_at', ''),
                        updated_at=item.get('updated_at', ''),
                        pushed_at=item.get('pushed_at', ''),
                        is_private=item.get('private', False),
                        is_fork=item.get('fork', False),
                        main_branch=item.get('default_branch', 'main')
                    )
                    repos.append(repo)
                    self.repositories[repo.name] = repo
                return repos
            except:
                return []
        return []
    
    def get_repository(self, owner: str, repo: str) -> Optional[Repository]:
        """Get repository details."""
        if not self.token:
            return None
        
        cmd = f'curl -H "Authorization: token {self.token}" -s {self.api_url}/repos/{owner}/{repo}'
        code, stdout, stderr = self._run_command(cmd)
        
        if code == 0:
            try:
                item = json.loads(stdout)
                repo = Repository(
                    owner=item['owner']['login'],
                    name=item['name'],
                    url=item['html_url'],
                    description=item.get('description', ''),
                    language=item.get('language'),
                    stars=item.get('stargazers_count', 0),
                    forks=item.get('forks_count', 0),
                    watchers=item.get('watchers_count', 0),
                    open_issues=item.get('open_issues_count', 0),
                    visibility=item.get('visibility', 'public'),
                    created_at=item.get('created_at', ''),
                    updated_at=item.get('updated_at', ''),
                    pushed_at=item.get('pushed_at', ''),
                    is_private=item.get('private', False),
                    is_fork=item.get('fork', False),
                    main_branch=item.get('default_branch', 'main')
                )
                return repo
            except:
                return None
        return None
    
    def list_issues(self, owner: str, repo: str, state: str = "open") -> List[Issue]:
        """List repository issues."""
        if not self.token:
            return []
        
        cmd = f'curl -H "Authorization: token {self.token}" -s "{self.api_url}/repos/{owner}/{repo}/issues?state={state}&per_page=30"'
        code, stdout, stderr = self._run_command(cmd)
        
        if code == 0:
            try:
                issues = []
                data = json.loads(stdout)
                for item in data:
                    if 'pull_request' not in item:  # Exclude PRs
                        issue = Issue(
                            number=item['number'],
                            title=item['title'],
                            body=item.get('body', ''),
                            state=item['state'],
                            user=item['user']['login'],
                            assignees=[a['login'] for a in item.get('assignees', [])],
                            labels=[l['name'] for l in item.get('labels', [])],
                            milestone=item['milestone']['title'] if item.get('milestone') else None,
                            created_at=item['created_at'],
                            updated_at=item['updated_at'],
                            closed_at=item.get('closed_at'),
                            url=item['html_url']
                        )
                        issues.append(issue)
                key = f"{owner}/{repo}"
                self.issues[key] = issues
                return issues
            except:
                return []
        return []
    
    def list_pull_requests(self, owner: str, repo: str, state: str = "open") -> List[PullRequest]:
        """List repository pull requests."""
        if not self.token:
            return []
        
        cmd = f'curl -H "Authorization: token {self.token}" -s "{self.api_url}/repos/{owner}/{repo}/pulls?state={state}&per_page=30"'
        code, stdout, stderr = self._run_command(cmd)
        
        if code == 0:
            try:
                prs = []
                data = json.loads(stdout)
                for item in data:
                    pr = PullRequest(
                        number=item['number'],
                        title=item['title'],
                        body=item.get('body', ''),
                        state=item['state'],
                        user=item['user']['login'],
                        assignees=[a['login'] for a in item.get('assignees', [])],
                        reviewers=[r['login'] for r in item.get('requested_reviewers', [])],
                        labels=[l['name'] for l in item.get('labels', [])],
                        created_at=item['created_at'],
                        updated_at=item['updated_at'],
                        merged_at=item.get('merged_at'),
                        head_branch=item['head']['ref'],
                        base_branch=item['base']['ref'],
                        additions=item.get('additions', 0),
                        deletions=item.get('deletions', 0),
                        changed_files=item.get('changed_files', 0),
                        commits=item.get('commits', 0),
                        url=item['html_url']
                    )
                    prs.append(pr)
                key = f"{owner}/{repo}"
                self.pull_requests[key] = prs
                return prs
            except:
                return []
        return []
    
    def create_issue(self, owner: str, repo: str, title: str, body: str = "", 
                    labels: List[str] = None, assignees: List[str] = None) -> bool:
        """Create issue in repository."""
        if not self.token:
            return False
        
        labels = labels or []
        assignees = assignees or []
        
        payload = json.dumps({
            "title": title,
            "body": body,
            "labels": labels,
            "assignees": assignees
        })
        
        cmd = f'curl -X POST -H "Authorization: token {self.token}" -H "Content-Type: application/json" -d \'{payload}\' -s {self.api_url}/repos/{owner}/{repo}/issues'
        code, stdout, stderr = self._run_command(cmd)
        
        return code == 0
    
    def create_pull_request(self, owner: str, repo: str, title: str, body: str = "",
                           head: str = "feature", base: str = "main", 
                           draft: bool = False) -> bool:
        """Create pull request in repository."""
        if not self.token:
            return False
        
        payload = json.dumps({
            "title": title,
            "body": body,
            "head": head,
            "base": base,
            "draft": draft
        })
        
        cmd = f'curl -X POST -H "Authorization: token {self.token}" -H "Content-Type: application/json" -d \'{payload}\' -s {self.api_url}/repos/{owner}/{repo}/pulls'
        code, stdout, stderr = self._run_command(cmd)
        
        return code == 0
    
    def list_workflow_runs(self, owner: str, repo: str, limit: int = 20) -> List[WorkflowRun]:
        """List workflow runs for repository."""
        if not self.token:
            return []
        
        cmd = f'curl -H "Authorization: token {self.token}" -s "{self.api_url}/repos/{owner}/{repo}/actions/runs?per_page={limit}"'
        code, stdout, stderr = self._run_command(cmd)
        
        if code == 0:
            try:
                runs = []
                data = json.loads(stdout)
                for item in data.get('workflow_runs', []):
                    run = WorkflowRun(
                        id=item['id'],
                        name=item['name'],
                        status=item['status'],
                        conclusion=item.get('conclusion'),
                        workflow_id=item['workflow_id'],
                        head_branch=item['head_branch'],
                        head_sha=item['head_sha'],
                        event=item['event'],
                        created_at=item['created_at'],
                        updated_at=item['updated_at'],
                        run_number=item['run_number'],
                        url=item['html_url']
                    )
                    runs.append(run)
                key = f"{owner}/{repo}"
                self.workflow_runs[key] = runs
                return runs
            except:
                return []
        return []
    
    def list_releases(self, owner: str, repo: str, limit: int = 20) -> List[Release]:
        """List releases for repository."""
        if not self.token:
            return []
        
        cmd = f'curl -H "Authorization: token {self.token}" -s "{self.api_url}/repos/{owner}/{repo}/releases?per_page={limit}"'
        code, stdout, stderr = self._run_command(cmd)
        
        if code == 0:
            try:
                releases = []
                data = json.loads(stdout)
                for item in data:
                    release = Release(
                        tag_name=item['tag_name'],
                        name=item.get('name', ''),
                        body=item.get('body', ''),
                        author=item['author']['login'],
                        created_at=item['created_at'],
                        published_at=item.get('published_at', ''),
                        draft=item['draft'],
                        prerelease=item['prerelease'],
                        asset_count=len(item.get('assets', [])),
                        download_url=item['html_url']
                    )
                    releases.append(release)
                key = f"{owner}/{repo}"
                self.releases[key] = releases
                return releases
            except:
                return []
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about cached data."""
        total_issues = sum(len(v) for v in self.issues.values())
        total_prs = sum(len(v) for v in self.pull_requests.values())
        total_runs = sum(len(v) for v in self.workflow_runs.values())
        total_releases = sum(len(v) for v in self.releases.values())
        
        return {
            'authenticated_user': self.current_user.login if self.current_user else None,
            'repositories_cached': len(self.repositories),
            'issues_cached': total_issues,
            'pull_requests_cached': total_prs,
            'workflow_runs_cached': total_runs,
            'releases_cached': total_releases
        }


# ===================== SINGLETON PATTERN =====================

_git_automation_service: Optional[GitHubAutomationService] = None


def get_github_automation_service(token: Optional[str] = None) -> GitHubAutomationService:
    """Get or create GitHub automation service singleton."""
    global _git_automation_service
    if _git_automation_service is None:
        _git_automation_service = GitHubAutomationService(token)
    return _git_automation_service


def reset_github_automation_service():
    """Reset GitHub automation service (for testing)."""
    global _git_automation_service
    _git_automation_service = None


# ===================== CLI COMMANDS =====================

def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1]
    
    # Initialize service
    token = os.environ.get('GITHUB_TOKEN')
    service = get_github_automation_service(token)
    
    if command == "auth":
        if service.authenticate():
            print(f"✓ Authenticated as: {service.current_user.login}")
            print(f"  Followers: {service.current_user.followers}")
            print(f"  Following: {service.current_user.following}")
            print(f"  Public repos: {service.current_user.public_repos}")
        else:
            print("✗ Authentication failed")
    
    elif command == "repos":
        repos = service.list_repositories()
        print(f"\n{len(repos)} Repositories Found:\n")
        for repo in repos:
            print(f"  {repo.name:30} | ⭐ {repo.stars:5} | 🔒 {repo.visibility:7} | {repo.language or 'N/A'}")
    
    elif command == "issues" and len(sys.argv) >= 4:
        owner, repo = sys.argv[2], sys.argv[3]
        state = sys.argv[4] if len(sys.argv) > 4 else "open"
        issues = service.list_issues(owner, repo, state)
        print(f"\n{len(issues)} Issues ({state}):\n")
        for issue in issues:
            print(f"  #{issue.number:4} | {issue.title:40} | {issue.state:8} | {issue.user}")
    
    elif command == "prs" and len(sys.argv) >= 4:
        owner, repo = sys.argv[2], sys.argv[3]
        state = sys.argv[4] if len(sys.argv) > 4 else "open"
        prs = service.list_pull_requests(owner, repo, state)
        print(f"\n{len(prs)} Pull Requests ({state}):\n")
        for pr in prs:
            print(f"  #{pr.number:4} | {pr.title:40} | {pr.state:8} | +{pr.additions} -{pr.deletions}")
    
    elif command == "workflows" and len(sys.argv) >= 4:
        owner, repo = sys.argv[2], sys.argv[3]
        runs = service.list_workflow_runs(owner, repo)
        print(f"\n{len(runs)} Workflow Runs:\n")
        for run in runs:
            conclusion = run.conclusion or "pending"
            print(f"  #{run.run_number:4} | {run.name:30} | {run.status:12} | {conclusion}")
    
    elif command == "stats":
        stats = service.get_statistics()
        print("\n📊 GitHub Automation Statistics:\n")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    else:
        print_help()


def print_help():
    """Print help message."""
    help_text = """
GitHub CLI Automation Toolkit
============================

USAGE:
  github_automation_toolkit.py <command> [args]

COMMANDS:
  auth                              Authenticate with GitHub (requires GITHUB_TOKEN env var)
  repos                             List your repositories
  issues <owner> <repo> [state]     List repository issues (state: open, closed, all)
  prs <owner> <repo> [state]        List repository pull requests
  workflows <owner> <repo>          List workflow runs
  stats                             Show cached statistics

ENVIRONMENT VARIABLES:
  GITHUB_TOKEN                      GitHub personal access token for authentication

EXAMPLES:
  python github_automation_toolkit.py auth
  python github_automation_toolkit.py repos
  python github_automation_toolkit.py issues microsoft vscode open
  python github_automation_toolkit.py prs python cpython merged
  python github_automation_toolkit.py workflows torvalds linux
  python github_automation_toolkit.py stats

NOTE:
  This toolkit provides GitHub CLI automation without requiring elevated
  permissions. Ensure GITHUB_TOKEN is set for authenticated requests.
    """
    print(help_text)


if __name__ == "__main__":
    main()
