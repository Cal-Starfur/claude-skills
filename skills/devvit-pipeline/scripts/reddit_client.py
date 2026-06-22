"""
tools/reddit_client.py — Reddit API Client
OAuth2 authenticated access to Reddit.
Handles token refresh automatically.

Usage:
    from tools.reddit_client import RedditClient
    reddit = RedditClient(
        client_id='your_client_id',
        client_secret='your_client_secret',
        username='your_reddit_username',
        password='your_reddit_password',
        user_agent='WigglersRoom/1.0'
    )
    posts = reddit.get_subreddit_posts('your_subreddit')
"""

import json
import base64
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta


class RedditClient:
    """
    Reddit OAuth2 API client.
    Auto-refreshes access token when expired.
    """

    OAUTH_BASE = 'https://oauth.reddit.com'
    AUTH_URL = 'https://www.reddit.com/api/v1/access_token'

    def __init__(self, client_id, client_secret, username, password,
                 user_agent='DevvitPipeline/1.0'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.user_agent = user_agent
        self._token = None
        self._token_expires = None

    # ── Auth ──────────────────────────────────────────────────────────────

    def _get_token(self):
        """Get or refresh OAuth2 access token."""
        if self._token and self._token_expires and datetime.now() < self._token_expires:
            return self._token

        credentials = base64.b64encode(
            f'{self.client_id}:{self.client_secret}'.encode()
        ).decode()

        data = urllib.parse.urlencode({
            'grant_type': 'password',
            'username': self.username,
            'password': self.password,
        }).encode()

        req = urllib.request.Request(
            self.AUTH_URL,
            data=data,
            headers={
                'Authorization': f'Basic {credentials}',
                'User-Agent': self.user_agent,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        )

        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            self._token = result['access_token']
            self._token_expires = datetime.now() + timedelta(seconds=result['expires_in'] - 60)
            return self._token

    def _headers(self):
        return {
            'Authorization': f'bearer {self._get_token()}',
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json',
        }

    def _get(self, endpoint, params=None):
        url = f'{self.OAUTH_BASE}{endpoint}'
        if params:
            url += '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise RedditError(e.code, endpoint)

    def _post(self, endpoint, data):
        url = f'{self.OAUTH_BASE}{endpoint}'
        encoded = urllib.parse.urlencode(data).encode()
        headers = self._headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        req = urllib.request.Request(url, data=encoded, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise RedditError(e.code, endpoint)

    # ── Subreddit ─────────────────────────────────────────────────────────

    def get_subreddit_posts(self, subreddit, sort='new', limit=10):
        """
        Get recent posts from a subreddit.
        sort: 'new' | 'hot' | 'top'
        Returns list of post dicts.
        """
        data = self._get(f'/r/{subreddit}/{sort}', {'limit': limit})
        posts = []
        for child in data['data']['children']:
            p = child['data']
            posts.append({
                'id': p['id'],
                'fullname': p['name'],
                'title': p['title'],
                'url': f"https://reddit.com{p['permalink']}",
                'author': p['author'],
                'score': p['score'],
                'num_comments': p['num_comments'],
                'created': datetime.fromtimestamp(p['created_utc']).strftime('%Y-%m-%d %H:%M'),
                'flair': p.get('link_flair_text', ''),
                'is_self': p['is_self'],
            })
        return posts

    def find_game_post(self, subreddit, title_contains='Wigglers'):
        """Find the game post in a subreddit by title keyword."""
        posts = self.get_subreddit_posts(subreddit, sort='new', limit=25)
        for post in posts:
            if title_contains.lower() in post['title'].lower():
                return post
        # Also check hot
        posts_hot = self.get_subreddit_posts(subreddit, sort='hot', limit=25)
        for post in posts_hot:
            if title_contains.lower() in post['title'].lower():
                return post
        return None

    # ── Comments ──────────────────────────────────────────────────────────

    def get_comments(self, subreddit, post_id, limit=25):
        """
        Get comments on a post.
        Returns list of comment dicts sorted by newest.
        """
        data = self._get(f'/r/{subreddit}/comments/{post_id}',
                        {'limit': limit, 'sort': 'new'})
        comments = []
        if len(data) > 1:
            for child in data[1]['data']['children']:
                c = child['data']
                if c.get('body') and c.get('author') != 'AutoModerator':
                    comments.append({
                        'id': c['id'],
                        'author': c['author'],
                        'body': c['body'],
                        'score': c['score'],
                        'created': datetime.fromtimestamp(c['created_utc']).strftime('%Y-%m-%d %H:%M'),
                    })
        return comments

    def get_new_comments_since(self, subreddit, post_id, since_minutes=30):
        """Get comments posted in the last N minutes."""
        comments = self.get_comments(subreddit, post_id, limit=50)
        cutoff = datetime.now() - timedelta(minutes=since_minutes)
        return [c for c in comments
                if datetime.strptime(c['created'], '%Y-%m-%d %H:%M') > cutoff]

    # ── Post Submission ───────────────────────────────────────────────────

    def submit_post(self, subreddit, title, text=None, url=None, flair=None):
        """
        Submit a new post to a subreddit.
        Either text (self post) or url (link post).
        Returns post dict with id and url.
        """
        data = {
            'sr': subreddit,
            'title': title,
            'kind': 'self' if text else 'link',
            'resubmit': True,
            'nsfw': False,
            'spoiler': False,
        }
        if text:
            data['text'] = text
        if url:
            data['url'] = url
        if flair:
            data['flair_text'] = flair

        result = self._post('/api/submit', data)
        if result.get('success') or 'url' in str(result):
            post_data = result.get('jquery', [])
            # Extract URL from response
            url_out = None
            for item in post_data:
                if isinstance(item, list) and len(item) > 3:
                    if isinstance(item[3], list):
                        for sub in item[3]:
                            if isinstance(sub, str) and 'reddit.com/r/' in sub:
                                url_out = sub
            return {'success': True, 'url': url_out, 'raw': result}
        return {'success': False, 'raw': result}

    def post_comment(self, parent_fullname, text):
        """Post a comment on a post or reply to a comment."""
        result = self._post('/api/comment', {
            'parent': parent_fullname,
            'text': text,
        })
        return result

    # ── User & App Info ───────────────────────────────────────────────────

    def get_my_posts(self, limit=10):
        """Get posts submitted by the authenticated user."""
        data = self._get(f'/user/{self.username}/submitted',
                        {'limit': limit, 'sort': 'new'})
        posts = []
        for child in data['data']['children']:
            p = child['data']
            posts.append({
                'id': p['id'],
                'title': p['title'],
                'subreddit': p['subreddit'],
                'url': f"https://reddit.com{p['permalink']}",
                'num_comments': p['num_comments'],
                'score': p['score'],
                'created': datetime.fromtimestamp(p['created_utc']).strftime('%Y-%m-%d %H:%M'),
            })
        return posts

    def get_post(self, post_fullname):
        """Get a specific post by fullname (t3_xxxxx)."""
        data = self._get('/api/info', {'id': post_fullname})
        children = data['data']['children']
        if children:
            p = children[0]['data']
            return {
                'id': p['id'],
                'title': p['title'],
                'score': p['score'],
                'num_comments': p['num_comments'],
                'url': f"https://reddit.com{p['permalink']}",
                'created': datetime.fromtimestamp(p['created_utc']).strftime('%Y-%m-%d %H:%M'),
            }
        return None

    def test_connection(self):
        """Verify credentials work."""
        data = self._get('/api/v1/me')
        print(f"✓ Reddit connected as: u/{data.get('name', 'unknown')}")
        print(f"  Karma: {data.get('total_karma', 0)}")
        return True


class RedditError(Exception):
    def __init__(self, status, endpoint):
        self.status = status
        self.endpoint = endpoint
        super().__init__(f"Reddit API {status}: {endpoint}")

