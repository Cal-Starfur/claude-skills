"""
tools/bridge_client.py — Codespace Bridge Client
Runs shell commands inside the Wigglers_Room GitHub Codespace
by relaying through the Cal-Starfur/codespace-bridge GitHub repo.

How it works:
  Claude writes {"cmd": "...", "id": "abc123"} to relay/inbox.json via GitHub API
  bridge3.js (running in Codespace) polls every 3s, runs the command
  bridge3.js writes {"id": "abc123", "stdout": "...", "ready": true} to relay/outbox.json
  Claude reads outbox.json and returns the result

Prerequisite: bridge3.js must be running in the Codespace:
  curl -o ~/bridge3.js https://raw.githubusercontent.com/Cal-Starfur/codespace-bridge/main/bridge3.js
  export BRIDGE_TOKEN=<github_pat>
  node ~/bridge3.js

Import:
    from tools.bridge_client import BridgeClient
    bridge = BridgeClient(token='ghp_...', owner='Cal-Starfur', repo='codespace-bridge')
    result = bridge.run("git pull")
    print(result['stdout'])
"""

import json
import uuid
import time
import base64
import urllib.request
import urllib.error
from datetime import datetime


class BridgeClient:
    """
    Relay shell commands to a GitHub Codespace via a GitHub repo inbox/outbox.

    The bridge repo (Cal-Starfur/codespace-bridge) stores:
      relay/inbox.json  — command Claude writes
      relay/outbox.json — result bridge3.js writes back
    """

    BASE = 'https://api.github.com'
    DEFAULT_CWD = '/workspaces/Wigglers_Room'

    def __init__(self, token, owner='Cal-Starfur', repo='codespace-bridge', branch='main'):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.base_repo = f'{self.BASE}/repos/{owner}/{repo}'

    def _headers(self):
        return {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
            'User-Agent': 'BridgeClient/1.0',
        }

    def _request(self, method, url, data=None):
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read()), resp.status
        except urllib.error.HTTPError as e:
            body_bytes = b''
            try:
                body_bytes = e.read()
            except:
                pass
            msg = ''
            try:
                msg = json.loads(body_bytes).get('message', str(e))
            except:
                msg = str(e)
            raise BridgeError(e.code, msg, url)

    def _read_file(self, path):
        """Read a file from the bridge repo. Returns (content_dict, sha)."""
        url = f'{self.base_repo}/contents/{path}?ref={self.branch}'
        try:
            data, _ = self._request('GET', url)
            raw = base64.b64decode(data['content']).decode('utf-8')
            content = json.loads(raw) if raw.strip() else {}
            return content, data['sha']
        except BridgeError as e:
            if e.status == 404:
                return {}, None
            raise

    def _write_file(self, path, content_dict, sha, commit_message):
        """Write a JSON dict to a file in the bridge repo."""
        raw = json.dumps(content_dict, indent=2)
        encoded = base64.b64encode(raw.encode('utf-8')).decode('utf-8')
        payload = {
            'message': commit_message,
            'content': encoded,
            'branch': self.branch,
        }
        if sha:
            payload['sha'] = sha
        url = f'{self.base_repo}/contents/{path}'
        self._request('PUT', url, payload)

    def run(self, cmd, cwd=None, timeout_polls=36, poll_interval=5):
        """
        Run a shell command in the Codespace via the bridge relay.

        Args:
            cmd: Shell command string to run (e.g. "git pull")
            cwd: Working directory in Codespace (default: /workspaces/Wigglers_Room)
            timeout_polls: Max number of polls before giving up (default 36 = 3 min)
            poll_interval: Seconds between polls (default 5)

        Returns:
            dict with keys: id, stdout, stderr, exit_code, ready, error (on timeout)

        Raises:
            BridgeError if GitHub API calls fail
        """
        cwd = cwd or self.DEFAULT_CWD
        cmd_id = str(uuid.uuid4())[:8]

        print(f'  [bridge] → {cmd[:80]}{"..." if len(cmd) > 80 else ""}')
        print(f'  [bridge]   id={cmd_id} cwd={cwd}')

        # Avoid SHA race condition from rapid successive writes
        time.sleep(2)

        # Write command to inbox
        _, inbox_sha = self._read_file('relay/inbox.json')
        self._write_file(
            'relay/inbox.json',
            {'cmd': cmd, 'id': cmd_id, 'cwd': cwd, 'ts': datetime.now().isoformat()},
            inbox_sha,
            f'bridge: [{cmd_id}] {cmd[:50]}'
        )

        print(f'  [bridge]   command written, polling outbox...')

        # Poll outbox for result
        for i in range(timeout_polls):
            time.sleep(poll_interval)
            outbox, _ = self._read_file('relay/outbox.json')

            if outbox.get('id') == cmd_id and outbox.get('ready'):
                stdout = outbox.get('stdout', '')
                exit_code = outbox.get('exit_code', 0)
                icon = '✓' if exit_code == 0 else '✗'
                print(f'  [bridge] {icon} done in {(i+1)*poll_interval}s (exit {exit_code})')
                if stdout:
                    # Print first 500 chars of output
                    preview = stdout[:500]
                    if len(stdout) > 500:
                        preview += f'\n... [{len(stdout)-500} more chars]' 
                    print(f'  {preview}')
                return outbox

            elapsed = (i + 1) * poll_interval
            print(f'  [bridge]   [{elapsed}s] waiting...')

        print(f'  [bridge] ✗ timeout after {timeout_polls * poll_interval}s')
        return {'id': cmd_id, 'error': 'timeout', 'ready': False}

    def check_bridge_alive(self):
        """
        Verify bridge3.js is running by checking if outbox has a recent heartbeat.
        Returns True if bridge appears active, False otherwise.
        """
        outbox, _ = self._read_file('relay/outbox.json')
        if not outbox:
            print('  [bridge] ⚠️  outbox is empty — bridge3.js may not be running')
            print('  Start it in Codespace: node ~/bridge3.js')
            return False
        print(f'  [bridge] ✓ outbox found (last id: {outbox.get("id", "none")})')
        return True

    def ping(self):
        """Send an echo command to confirm bridge roundtrip works."""
        print('  [bridge] Pinging bridge...')
        result = self.run('echo BRIDGE_OK', timeout_polls=12)
        if result.get('stdout', '').strip() == 'BRIDGE_OK':
            print('  [bridge] ✓ Bridge roundtrip confirmed')
            return True
        print(f'  [bridge] ✗ Ping failed: {result}')
        return False


class BridgeError(Exception):
    def __init__(self, status, message, url=''):
        self.status = status
        self.message = message
        self.url = url
        super().__init__(f'Bridge/GitHub API {status}: {message}')
