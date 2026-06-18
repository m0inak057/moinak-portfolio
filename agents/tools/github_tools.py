import requests
import base64

def fetch_all_repos(username: str, token: str) -> list[dict]:
    """
    Returns list of repo dicts from GitHub API.
    Handles pagination — fetches ALL pages.
    Each dict contains: id, name, html_url, description, updated_at, pushed_at
    """
    headers = {"Authorization": f"token {token}"}
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def fetch_readme(repo_url: str, token: str) -> str:
    """
    Given a GitHub repo HTML URL (e.g. https://github.com/user/repo),
    fetches the raw README.md content.
    Returns empty string if no README exists.
    """
    # Extract owner/repo from URL
    parts = repo_url.rstrip("/").split("/")
    owner, repo = parts[-2], parts[-1]
    
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 404:
        return ""
    
    resp.raise_for_status()
    content = resp.json().get("content", "")
    return base64.b64decode(content).decode("utf-8", errors="replace")
