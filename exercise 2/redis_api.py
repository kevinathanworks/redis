#!/usr/bin/env python3
"""
Redis Enterprise Exercise 2 — Working with Redis REST API

Steps performed:
  1. Create a new Redis database (no modules)
  2. Create three new users with specified roles
  3. List and display all users
  4. Delete the created database

Usage:
    pip install requests
    python redis_api.py --username admin@example.com --password yourpassword
"""

import argparse
import sys
import requests
import urllib3

# Suppress SSL warnings for self-signed cluster certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Configuration ────────────────────────────────────────────────────────────
DEFAULT_BASE_URL = "https://re-cluster1.ps-redislabs.org:9443"
DEFAULT_IP_URL   = "https://<cluster-ip>:9443"   # fallback if hostname fails

DB_NAME      = "exercise2-db"
DB_MEMORY_GB = 1   # 1 GB

USERS_TO_CREATE = [
    {"email": "john.doe@example.com",   "name": "John Doe",      "role": "db_viewer"},
    {"email": "mike.smith@example.com", "name": "Mike Smith",    "role": "db_member"},
    {"email": "cary.johnson@example.com","name": "Cary Johnson", "role": "admin"},
]
# ─────────────────────────────────────────────────────────────────────────────


def build_session(username: str, password: str) -> requests.Session:
    session = requests.Session()
    session.auth = (username, password)
    session.verify = False
    session.headers.update({"Content-Type": "application/json"})
    return session


def create_database(session: requests.Session, base_url: str) -> int:
    """Create a new Redis database with no modules. Returns the database uid."""
    payload = {
        "name": DB_NAME,
        "type": "redis",
        "memory_size": DB_MEMORY_GB * 1024 * 1024 * 1024,
        "shards_count": 1,
    }
    resp = session.post(f"{base_url}/v1/bdbs", json=payload)
    resp.raise_for_status()
    db = resp.json()
    print(f"[+] Database created  : {db['name']}  (uid={db['uid']}, port={db.get('port', 'N/A')})")
    return db["uid"]


def create_users(session: requests.Session, base_url: str, user_password: str) -> list[int]:
    """Create three users. Returns list of created user uids."""
    created = []
    for user in USERS_TO_CREATE:
        payload = {
            "email":    user["email"],
            "name":     user["name"],
            "role":     user["role"],
            "password": user_password,
        }
        resp = session.post(f"{base_url}/v1/users", json=payload)
        resp.raise_for_status()
        u = resp.json()
        print(f"[+] User created      : {u['name']:<20}  role={u['role']:<12}  {u['email']}")
        created.append(u["uid"])
    return created


def list_users(session: requests.Session, base_url: str) -> None:
    """Fetch all users and display name, role, and email."""
    resp = session.get(f"{base_url}/v1/users")
    resp.raise_for_status()
    users = resp.json()

    print(f"\n{'─' * 62}")
    print(f"  {'Name':<22} {'Role':<16} Email")
    print(f"{'─' * 62}")
    for u in users:
        print(f"  {u.get('name', ''):<22} {u.get('role', ''):<16} {u.get('email', '')}")
    print(f"{'─' * 62}")
    print(f"  Total users: {len(users)}\n")


def delete_database(session: requests.Session, base_url: str, uid: int) -> None:
    """Delete the database by uid."""
    resp = session.delete(f"{base_url}/v1/bdbs/{uid}")
    resp.raise_for_status()
    print(f"[+] Database deleted  : uid={uid}")


def main():
    parser = argparse.ArgumentParser(description="Redis Enterprise REST API — Exercise 2")
    parser.add_argument("--url",           default=DEFAULT_BASE_URL,
                        help="Redis Enterprise cluster URL (default: %(default)s)")
    parser.add_argument("--username",      required=True,
                        help="Cluster admin email")
    parser.add_argument("--password",      required=True,
                        help="Cluster admin password")
    parser.add_argument("--user-password", default="Redis1234!",
                        help="Password assigned to each created user (default: Redis1234!)")
    args = parser.parse_args()

    session = build_session(args.username, args.password)

    print(f"\nConnecting to: {args.url}\n")

    # Step 1 — Create database
    db_uid = create_database(session, args.url)

    # Step 2 — Create users
    print()
    create_users(session, args.url, args.user_password)

    # Step 3 — List all users
    list_users(session, args.url)

    # Step 4 — Delete database
    delete_database(session, args.url, db_uid)

    print("\nDone.")


if __name__ == "__main__":
    main()
