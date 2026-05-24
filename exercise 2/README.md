# Redis Enterprise Exercise 2 — Working with Redis REST API

This script uses the Redis Enterprise REST API to create a database, manage users, and clean up — all programmatically without touching the Admin UI.

**API Reference:** https://redis.io/docs/latest/operate/rs/references/rest-api/

---

## Project Structure

```
exercise 2/
├── redis_api.py       # Main Python script
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

---

## Prerequisites

- Python 3.x
- Access to a Redis Enterprise cluster
- Cluster admin credentials

Install dependencies:

```bash
pip install -r requirements.txt
```

> **Note:** This cluster uses RBAC (Role-Based Access Control). Users are assigned roles via `role_uids` instead of a plain `role` string. The script automatically creates any missing roles before creating users and is safe to re-run (it cleans up existing users first).

---

## What the Script Does

1. **Creates a new database** — single-shard, 1 GB, no modules
2. **Creates three users** with the following roles:

| Name | Email | Role |
|---|---|---|
| John Doe | john.doe@example.com | db_viewer |
| Mike Smith | mike.smith@example.com | db_member |
| Cary Johnson | cary.johnson@example.com | admin |

3. **Lists and displays all users** in a formatted table (name, role, email)
4. **Deletes the created database**

---

## Usage

```bash
python redis_api.py --username admin@example.com --password yourpassword
```

### All options

| Flag | Description | Default |
|---|---|---|
| `--url` | Cluster REST API URL | `https://re-cluster1.ps-redislabs.org:9443` |
| `--username` | Cluster admin email | *(required)* |
| `--password` | Cluster admin password | *(required)* |
| `--user-password` | Password assigned to each created user | `Redis1234!` |

### Using the IP address (if hostname doesn't resolve)

```bash
python redis_api.py \
  --url https://<cluster-ip>:9443 \
  --username admin@example.com \
  --password yourpassword
```

---

## Example Output

```
Connecting to: https://re-cluster1.ps-redislabs.org:9443

[+] Database created  : exercise2-db  (uid=5, port=12005)

[+] User created      : John Doe              role=db_viewer   john.doe@example.com
[+] User created      : Mike Smith            role=db_member   mike.smith@example.com
[+] User created      : Cary Johnson          role=admin       cary.johnson@example.com

──────────────────────────────────────────────────────────────
  Name                   Role             Email
──────────────────────────────────────────────────────────────
  admin                  admin            admin@example.com
  John Doe               db_viewer        john.doe@example.com
  Mike Smith             db_member        mike.smith@example.com
  Cary Johnson           admin            cary.johnson@example.com
──────────────────────────────────────────────────────────────
  Total users: 4

[+] Database deleted  : uid=5

Done.
```

---

## API Endpoints Used

| Action | Method | Endpoint |
|---|---|---|
| Create database | `POST` | `/v1/bdbs` |
| Create user | `POST` | `/v1/users` |
| List all users | `GET` | `/v1/users` |
| Delete database | `DELETE` | `/v1/bdbs/{uid}` |

> **Note:** SSL verification is disabled in the script (`verify=False`) because Redis Enterprise clusters typically use self-signed certificates. Do not disable SSL verification in production environments with valid certificates.
