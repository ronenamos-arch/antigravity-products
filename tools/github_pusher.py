"""
github_pusher.py — Push a product folder (HTML + images) to GitHub repo,
then trigger a Vercel deployment via API.
"""

import base64
import os
import time
import requests
from pathlib import Path
from github import Github, Auth, GithubException
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
VERCEL_PROJECT_ID = os.getenv("VERCEL_PROJECT_ID")
VERCEL_TEAM_ID = os.getenv("VERCEL_TEAM_ID")


def push_product(slug: str, products_dir: str = "products") -> str:
    print(f"[debug] Token starts with: {str(GITHUB_TOKEN)[:5]}")
    if not all([GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO]):
        raise ValueError("Missing GitHub credentials in .env")

    g = Github(auth=Auth.Token(GITHUB_TOKEN))
    repo = g.get_repo(f"{GITHUB_OWNER}/{GITHUB_REPO}")
    product_path = Path(products_dir) / slug

    if not product_path.exists():
        raise FileNotFoundError(f"Product folder not found: {product_path}")

    files_pushed = 0
    files_updated = 0

    # Push vercel.json to repo root first (if not there)
    try:
        repo.get_contents("vercel.json")
    except GithubException:
        vercel_config = '{\n  "cleanUrls": true,\n  "trailingSlash": false\n}'
        repo.create_file("vercel.json", "Add Vercel config", vercel_config.encode())
        print("[github] Created: vercel.json")

    for file_path in sorted(product_path.rglob("*")):
        if file_path.is_dir():
            continue

        github_path = f"products/{slug}/{file_path.relative_to(product_path).as_posix()}"

        with open(file_path, "rb") as f:
            content = f.read()

        commit_message = f"Add/update {github_path}"

        try:
            existing = repo.get_contents(github_path)
            repo.update_file(github_path, commit_message, content, existing.sha)
            print(f"[github] Updated: {github_path}")
            files_updated += 1
        except GithubException as e:
            if e.status == 404:
                repo.create_file(github_path, commit_message, content)
                print(f"[github] Created: {github_path}")
                files_pushed += 1
            else:
                raise

    print(f"\n[github] Done: {files_pushed} created, {files_updated} updated")
    return trigger_vercel_deploy(slug, products_dir)


def trigger_vercel_deploy(slug: str, products_dir: str = "products") -> str:
    if not VERCEL_TOKEN or not VERCEL_PROJECT_ID:
        return f"https://antigravity-products.vercel.app/products/{slug}"

    print("\n[vercel] Triggering deployment...")

    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"}
    params = {"teamId": VERCEL_TEAM_ID} if VERCEL_TEAM_ID else {}

    products_path = Path(products_dir) / slug
    files = []

    for file_path in sorted(products_path.rglob("*")):
        if file_path.is_dir():
            continue
        rel = f"products/{slug}/{file_path.relative_to(products_path).as_posix()}"
        with open(file_path, "rb") as f:
            raw = f.read()
        files.append({"file": rel, "data": base64.b64encode(raw).decode(), "encoding": "base64"})

    files.append({
        "file": "vercel.json",
        "data": base64.b64encode(b'{\n  "cleanUrls": true,\n  "trailingSlash": false\n}').decode(),
        "encoding": "base64"
    })

    resp = requests.post(
        "https://api.vercel.com/v13/deployments",
        headers=headers, params=params,
        json={"name": "antigravity-products", "files": files, "target": "production"},
        timeout=60,
    )

    if resp.status_code in (200, 201):
        data = resp.json()
        deploy_id = data.get("id", "")
        deploy_url = data.get("url", "")
        print(f"[vercel] Deployment triggered: {deploy_id}")

        for _ in range(18):
            time.sleep(5)
            check = requests.get(f"https://api.vercel.com/v13/deployments/{deploy_id}", headers=headers, params=params)
            state = check.json().get("readyState", "")
            print(f"[vercel] Status: {state}")
            if state in ("READY", "ERROR", "CANCELED"):
                break

        live_url = f"https://{deploy_url}/products/{slug}" if deploy_url else f"https://antigravity-products.vercel.app/products/{slug}"
        print(f"[vercel] Live URL: {live_url}")
        return live_url
    else:
        print(f"[vercel] Deploy failed ({resp.status_code}): {resp.text[:200]}")
        return f"https://antigravity-products.vercel.app/products/{slug}"


if __name__ == "__main__":
    import sys
    url = push_product(sys.argv[1])
    print(f"\nLive at: {url}")
