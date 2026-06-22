"""
tools/github_client.py — GitHub API Client
Full read/write access to a GitHub repository.

Import:
    from tools.github_client import GitHubClient
    gh = GitHubClient(token='ghp_...', owner='yourname', repo='wigglers')
"""

import json
import base64
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime


class GitHubClient:
    """
    Full GitHub REST API client.
    Supports: read files, write files, create branches, open PRs, commit history.
    """

    BASE = 'https://api.github.com'

    def __init__(self, token, owner, repo, default_branch='main'):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.default_branch = default_branch
        self.base_repo = f"{self.BASE}/repos/{owner}/{repo}"

    def _headers(self):
        return {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
            'User-Agent': 'LeadDevSkill/1.0',
        }

    def _request(self, method, url, data=None):
        """Make an authenticated GitHub API request."""
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read()), resp.status
        except urllib.error.HTTPError as e:
            error_body = {}
            try:
                error_body = json.loads(e.read())
            except:
                pass
            raise GitHubError(e.code, error_body.get('message', str(e)), url)

    # ── Read Operations ────────────────────────────────────────────────────

    def get_file(self, path, branch=None):
        """
        Get file content from repo.
        Returns: {'content': str, 'sha': str, 'path': str, 'size': int}
        """
        branch = branch or self.default_branch
        url = f"{self.base_repo}/contents/{path}?ref={branch}"
        data, _ = self._request('GET', url)
        content = base64.b64decode(data['content']).decode('utf-8', errors='replace')
        return {
            'content': content,
            'sha': data['sha'],
            'path': data['path'],
            'size': data['size'],
            'url': data['html_url'],
        }

    def file_exists(self, path, branch=None):
        """Check if a file exists in the repo."""
        try:
            self.get_file(path, branch)
            return True
        except GitHubError as e:
            if e.status == 404:
                return False
            raise

    def list_files(self, path='', branch=None):
        """
        List files/directories at a path.
        Returns list of {'name', 'path', 'type' (file|dir), 'size'}
        """
        branch = branch or self.default_branch
        url = f"{self.base_repo}/contents/{path}?ref={branch}"
        data, _ = self._request('GET', url)
        if isinstance(data, list):
            return [{'name': f['name'], 'path': f['path'],
                     'type': f['type'], 'size': f.get('size', 0)} for f in data]
        return []

    def get_branch(self, branch=None):
        """Get branch info including latest commit SHA."""
        branch = branch or self.default_branch
        url = f"{self.base_repo}/branches/{branch}"
        data, _ = self._request('GET', url)
        return {
            'name': data['name'],
            'sha': data['commit']['sha'],
            'commit_url': data['commit']['url'],
        }

    def get_commit_history(self, path=None, branch=None, limit=10):
        """
        Get recent commits, optionally for a specific file.
        Returns list of {'sha', 'message', 'author', 'date'}
        """
        branch = branch or self.default_branch
        url = f"{self.base_repo}/commits?sha={branch}&per_page={limit}"
        if path:
            url += f"&path={path}"
        data, _ = self._request('GET', url)
        return [{
            'sha': c['sha'][:7],
            'message': c['commit']['message'].split('\n')[0],
            'author': c['commit']['author']['name'],
            'date': c['commit']['author']['date'][:10],
        } for c in data]

    # ── Write Operations ───────────────────────────────────────────────────

    def write_file(self, path, content, commit_message, branch=None, sha=None):
        """
        Create or update a file in the repo.
        If file exists, sha must be provided (get it from get_file()).
        Returns: {'commit_sha', 'file_url', 'branch'}
        """
        branch = branch or self.default_branch

        # Auto-get SHA if file exists and sha not provided
        if sha is None and self.file_exists(path, branch):
            existing = self.get_file(path, branch)
            sha = existing['sha']

        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        payload = {
            'message': commit_message,
            'content': encoded,
            'branch': branch,
        }
        if sha:
            payload['sha'] = sha

        url = f"{self.base_repo}/contents/{path}"
        data, _ = self._request('PUT', url, payload)
        return {
            'commit_sha': data['commit']['sha'][:7],
            'file_url': data['content']['html_url'],
            'branch': branch,
            'path': path,
        }

    def delete_file(self, path, commit_message, branch=None):
        """Delete a file from the repo."""
        branch = branch or self.default_branch
        existing = self.get_file(path, branch)
        payload = {
            'message': commit_message,
            'sha': existing['sha'],
            'branch': branch,
        }
        url = f"{self.base_repo}/contents/{path}"
        data, _ = self._request('DELETE', url, payload)
        return {'commit_sha': data['commit']['sha'][:7]}

    # ── Branch Operations ──────────────────────────────────────────────────

    def create_branch(self, branch_name, from_branch=None):
        """Create a new branch from an existing one."""
        from_branch = from_branch or self.default_branch
        source = self.get_branch(from_branch)
        url = f"{self.base_repo}/git/refs"
        payload = {
            'ref': f'refs/heads/{branch_name}',
            'sha': source['sha'],
        }
        try:
            data, _ = self._request('POST', url, payload)
            return {'branch': branch_name, 'sha': source['sha']}
        except GitHubError as e:
            if e.status == 422:  # Branch already exists
                return {'branch': branch_name, 'sha': source['sha'], 'existed': True}
            raise

    def branch_exists(self, branch_name):
        """Check if a branch exists."""
        try:
            self.get_branch(branch_name)
            return True
        except GitHubError as e:
            if e.status == 404:
                return False
            raise

    # ── Pull Request Operations ────────────────────────────────────────────

    def create_pull_request(self, title, body, head_branch, base_branch=None):
        """
        Open a pull request.
        Returns: {'number', 'url', 'title'}
        """
        base_branch = base_branch or self.default_branch
        url = f"{self.base_repo}/pulls"
        payload = {
            'title': title,
            'body': body,
            'head': head_branch,
            'base': base_branch,
        }
        data, _ = self._request('POST', url, payload)
        return {
            'number': data['number'],
            'url': data['html_url'],
            'title': data['title'],
            'state': data['state'],
        }

    def list_pull_requests(self, state='open'):
        """List PRs. state: 'open' | 'closed' | 'all'"""
        url = f"{self.base_repo}/pulls?state={state}&per_page=10"
        data, _ = self._request('GET', url)
        return [{
            'number': pr['number'],
            'title': pr['title'],
            'url': pr['html_url'],
            'branch': pr['head']['ref'],
            'created': pr['created_at'][:10],
        } for pr in data]

    # ── Repo Info ──────────────────────────────────────────────────────────

    def get_repo_info(self):
        """Get basic repo information."""
        data, _ = self._request('GET', self.base_repo)
        return {
            'name': data['name'],
            'description': data.get('description', ''),
            'default_branch': data['default_branch'],
            'private': data['private'],
            'url': data['html_url'],
            'last_push': data['pushed_at'][:10],
        }

    def test_connection(self):
        """Verify credentials and repo access. Returns True or raises."""
        info = self.get_repo_info()
        print(f"✓ Connected to: {self.owner}/{self.repo}")
        print(f"  Branch: {info['default_branch']}")
        print(f"  Last push: {info['last_push']}")
        return True


class GitHubError(Exception):
    def __init__(self, status, message, url=''):
        self.status = status
        self.message = message
        self.url = url
        super().__init__(f"GitHub API {status}: {message}")

