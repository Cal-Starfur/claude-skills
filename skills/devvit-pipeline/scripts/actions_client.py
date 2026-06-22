"""
tools/actions_client.py — GitHub Actions API Client
Trigger workflows, poll status, read logs.
Used to run devvit upload remotely after code push.

Usage:
    from tools.actions_client import ActionsClient
    actions = ActionsClient(token='ghp_...', owner='Cal-Starfur', repo='Wigglers_Room')
    run = actions.trigger_workflow('deploy.yml')
    result = actions.wait_for_completion(run['run_id'])
"""

import json
import time
import urllib.request
import urllib.error
import zipfile
import io
from datetime import datetime


class ActionsClient:
    """GitHub Actions API — trigger and monitor workflows."""

    BASE = 'https://api.github.com'

    def __init__(self, token, owner, repo):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_repo = f'{self.BASE}/repos/{owner}/{repo}'

    def _headers(self):
        return {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
            'User-Agent': 'DevvitPipeline/1.0',
        }

    def _request(self, method, url, data=None):
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body,
                                      headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                content = resp.read()
                return json.loads(content) if content else {}, resp.status
        except urllib.error.HTTPError as e:
            body = {}
            try:
                body = json.loads(e.read())
            except:
                pass
            raise ActionsError(e.code, body.get('message', str(e)), url)

    # ── Workflow Management ───────────────────────────────────────────────

    def list_workflows(self):
        """List all workflows in the repo."""
        data, _ = self._request('GET', f'{self.base_repo}/actions/workflows')
        return [{
            'id': w['id'],
            'name': w['name'],
            'filename': w['path'].split('/')[-1],
            'state': w['state'],
        } for w in data.get('workflows', [])]

    def get_workflow_id(self, filename):
        """Get workflow ID by filename (e.g. 'deploy.yml')."""
        workflows = self.list_workflows()
        for w in workflows:
            if w['filename'] == filename:
                return w['id']
        return None

    def trigger_workflow(self, workflow_filename, branch='main', inputs=None):
        """
        Trigger a workflow dispatch event.
        Returns run info dict with run_id to poll.
        """
        workflow_id = self.get_workflow_id(workflow_filename)
        if not workflow_id:
            raise ActionsError(404, f"Workflow '{workflow_filename}' not found", '')

        payload = {'ref': branch}
        if inputs:
            payload['inputs'] = inputs

        self._request('POST',
            f'{self.base_repo}/actions/workflows/{workflow_id}/dispatches',
            payload
        )

        # Wait a moment then find the new run
        time.sleep(3)
        runs = self.get_recent_runs(workflow_id, limit=1)
        if runs:
            return runs[0]
        return {'workflow': workflow_filename, 'status': 'triggered'}

    # ── Run Monitoring ────────────────────────────────────────────────────

    def get_recent_runs(self, workflow_id=None, limit=5, branch='main'):
        """Get recent workflow runs."""
        url = f'{self.base_repo}/actions/runs?per_page={limit}&branch={branch}'
        if workflow_id:
            url += f'&workflow_id={workflow_id}'
        data, _ = self._request('GET', url)
        runs = []
        for r in data.get('workflow_runs', []):
            runs.append({
                'run_id': r['id'],
                'name': r['name'],
                'status': r['status'],        # queued, in_progress, completed
                'conclusion': r['conclusion'], # success, failure, cancelled, None
                'branch': r['head_branch'],
                'commit': r['head_sha'][:7],
                'created': r['created_at'][:16].replace('T', ' '),
                'updated': r['updated_at'][:16].replace('T', ' '),
                'url': r['html_url'],
            })
        return runs

    def get_run_status(self, run_id):
        """Get current status of a specific run."""
        data, _ = self._request('GET', f'{self.base_repo}/actions/runs/{run_id}')
        return {
            'run_id': run_id,
            'status': data['status'],
            'conclusion': data.get('conclusion'),
            'name': data['name'],
            'commit': data['head_sha'][:7],
            'url': data['html_url'],
            'duration_seconds': None,
        }

    def wait_for_completion(self, run_id, timeout_seconds=300, poll_interval=8):
        """
        Poll a run until it completes or times out.
        Returns final run status dict.
        Prints progress updates.
        """
        start = time.time()
        print(f"Waiting for run {run_id}...")

        while True:
            elapsed = int(time.time() - start)
            if elapsed > timeout_seconds:
                print(f"Timeout after {elapsed}s")
                return {'run_id': run_id, 'status': 'timeout', 'conclusion': None}

            status = self.get_run_status(run_id)

            if status['status'] == 'completed':
                conclusion = status['conclusion']
                icon = '✓' if conclusion == 'success' else '✗'
                print(f"{icon} Completed in {elapsed}s — {conclusion}")
                return status

            print(f"  [{elapsed}s] {status['status']}...")
            time.sleep(poll_interval)

    # ── Logs ─────────────────────────────────────────────────────────────

    def get_run_logs(self, run_id, max_lines=100):
        """
        Download and extract run logs.
        Returns log text (last max_lines lines).
        """
        url = f'{self.base_repo}/actions/runs/{run_id}/logs'
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req) as resp:
                zip_data = resp.read()

            # Extract from zip
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                all_logs = []
                for name in zf.namelist():
                    with zf.open(name) as f:
                        content = f.read().decode('utf-8', errors='replace')
                        all_logs.append(f"=== {name} ===\n{content}")

            combined = '\n'.join(all_logs)
            lines = combined.split('\n')
            # Return last N lines (most relevant)
            return '\n'.join(lines[-max_lines:])

        except urllib.error.HTTPError as e:
            if e.code == 410:
                return "Logs expired (>90 days old)"
            raise

    def get_job_logs(self, run_id):
        """Get logs broken down by job and step."""
        data, _ = self._request('GET',
            f'{self.base_repo}/actions/runs/{run_id}/jobs')
        jobs = []
        for job in data.get('jobs', []):
            steps = [{
                'name': s['name'],
                'status': s['status'],
                'conclusion': s.get('conclusion'),
                'number': s['number'],
            } for s in job.get('steps', [])]
            jobs.append({
                'name': job['name'],
                'status': job['status'],
                'conclusion': job.get('conclusion'),
                'steps': steps,
            })
        return jobs

    # ── Workflow File Creator ─────────────────────────────────────────────

    def generate_deploy_workflow(self, devvit_token_secret='DEVVIT_TOKEN'):
        """
        Generate a GitHub Actions workflow YAML for Devvit deployment.
        Push this to .github/workflows/deploy.yml in the repo.

        The workflow:
        1. Triggers on push to main OR manual dispatch
        2. Installs Node + dependencies
        3. Runs devvit upload using a stored secret
        """
        return f"""name: Deploy to Devvit

on:
  push:
    branches: [ main ]
  workflow_dispatch:
    inputs:
      reason:
        description: 'Reason for manual deploy'
        required: false
        default: 'Manual deploy from Claude'

jobs:
  deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Devvit CLI
        run: npm install -g devvit

      - name: Authenticate Devvit
        run: |
          echo "Authenticating with Devvit..."
          devvit login --token ${{{{ secrets.{devvit_token_secret} }}}}

      - name: Upload to Devvit
        run: |
          echo "Deploying Wigglers Room..."
          devvit upload
          echo "Deploy complete"

      - name: Report status
        if: always()
        run: |
          echo "Workflow: ${{{{ github.workflow }}}}"
          echo "Commit: ${{{{ github.sha }}}}"
          echo "Status: ${{{{ job.status }}}}"
"""


class ActionsError(Exception):
    def __init__(self, status, message, url=''):
        self.status = status
        self.message = message
        super().__init__(f"Actions API {status}: {message}")

