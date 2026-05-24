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
    python redis_api.py --username admin@rl.org --password vYc80CA
"""

import argparse
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://re-cluster1.ps-redislabs.org:9443"

ROLES_NEEDED = ["db_viewer", "db_member", "admin"]

USERS_TO_CREATE = [
    {"email": "john.doe@example.com",    "name": "John Doe",      "role": "db_viewer"},
    {"email": "mike.smith@example.com",  "name": "Mike Smith",    "role": "db_member"},
    {"email": "cary.johnson@example.com","name": "Cary Johnson",  "role": "admin"},
]


def build_session(username: str, password: str) -> requests.Session:
    session = requests.Session()
    session.auth = (username, password)
    session.verify = False
    session.headers.update({"Content-Type": "application/json"})
    return session


def get_or_create_roles(session: requests.Session) -> dict:
    """Ensure all required roles exist. Returns a name->uid map."""
    resp = session.get(f"{BASE_URL}/v1/roles")
    resp.raise_for_status()
    existing = {r["name"].lower(): r["uid"] for r in resp.json()}

    role_map = {}
    for role_name in ROLES_NEEDED:
        if role_name in existing:
            role_map[role_name] = existing[role_name]
            print(f"[~] Role exists       : {role_name} (uid={existing[role_name]})")
        else:
            r = session.post(f"{BASE_URL}/v1/roles", json={
                "name": role_name,
                "management": role_name
            })
            r.raise_for_status()
            uid = r.json()["uid"]
            role_map[role_name] = uid
            print(f"[+] Role created      : {role_name} (uid={uid})")
    return role_map


def cleanup_existing_users(session: requests.Session) -> None:
    """Delete any previously created exercise users so the script is re-runnable."""
    emails = {u["email"] for u in USERS_TO_CREATE}
    resp = session.get(f"{BASE_URL}/v1/users")
    resp.raise_for_status()
    for u in resp.json():
        if u.get("email") in emails:
            session.delete(f"{BASE_URL}/v1/users/{u['uid']}")
            print(f"[~] Removed old user  : {u['email']}")


def create_database(session: requests.Session) -> int:
    """Create a new Redis database with no modules. Returns the database uid."""
    resp = session.post(f"{BASE_URL}/v1/bdbs", json={
        "name": "exercise2-db",
        "type": "redis",
        "memory_size": 1 * 1024 * 1024 * 1024,
        "shards_count": 1,
    })
    resp.raise_for_status()
    db = resp.json()
    print(f"[+] Database created  : {db['name']}  (uid={db['uid']})")
    return db["uid"]


def create_users(session: requests.Session, role_map: dict, user_password: str) -> None:
    """Create three users using role_uids (RBAC-enabled cluster)."""
    for user in USERS_TO_CREATE:
        resp = session.post(f"{BASE_URL}/v1/users", json={
            "email":     user["email"],
            "name":      user["name"],
            "role_uids": [role_map[user["role"]]],
            "password":  user_password,
        })
        resp.raise_for_status()
        u = resp.json()
        print(f"[+] User created      : {u['name']:<20}  role={user['role']:<12}  {u['email']}")


def list_users(session: requests.Session, role_map: dict) -> None:
    """Fetch all users and display name, role, and email."""
    uid_to_role = {v: k for k, v in role_map.items()}
    resp = session.get(f"{BASE_URL}/v1/users")
    resp.raise_for_status()
    users = resp.json()

    print(f"\n{'-' * 65}")
    print(f"  {'Name':<22} {'Role':<16} Email")
    print(f"{'-' * 65}")
    for u in users:
        role_uids = u.get("role_uids", [])
        role_name = uid_to_role.get(role_uids[0], "unknown") if role_uids else u.get("role", "unknown")
        print(f"  {u.get('name', ''):<22} {role_name:<16} {u.get('email', '')}")
    print(f"{'-' * 65}")
    print(f"  Total users: {len(users)}\n")


def delete_database(session: requests.Session, uid: int) -> None:
    """Wait for database to be active then delete it."""
    print("Waiting for database to be ready before deleting...")
    time.sleep(5)
    resp = session.delete(f"{BASE_URL}/v1/bdbs/{uid}")
    resp.raise_for_status()
    print(f"[+] Database deleted  : uid={uid}")


def main():
    parser = argparse.ArgumentParser(description="Redis Enterprise REST API — Exercise 2")
    parser.add_argument("--username",      required=True)
    parser.add_argument("--password",      required=True)
    parser.add_argument("--user-password", default="Redis1234!")
    args = parser.parse_args()

    session = build_session(args.username, args.password)
    print(f"\nConnecting to: {BASE_URL}\n")

    role_map = get_or_create_roles(session)
    print()
    cleanup_existing_users(session)
    print()
    db_uid = create_database(session)
    print()
    create_users(session, role_map, args.user_password)
    list_users(session, role_map)
    delete_database(session, db_uid)
    print("\nDone.")


if __name__ == "__main__":
    main()
