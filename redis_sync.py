#!/usr/bin/env python3
"""
Redis Enterprise Exercise 1 — Building and Synchronizing Redis Databases

Inserts values 1-100 into source-db using a Redis List, then reads and
prints them in reverse order from replica-db.

Usage:
    pip install redis
    python redis_sync.py [--source-host HOST] [--source-port PORT]
                         [--replica-host HOST] [--replica-port PORT]
"""

import argparse
import time
import sys

import redis

# ── Defaults (override via CLI args or environment) ─────────────────────────
DEFAULT_SOURCE_HOST  = "localhost"
DEFAULT_SOURCE_PORT  = 6379
DEFAULT_REPLICA_HOST = "localhost"
DEFAULT_REPLICA_PORT = 6380
LIST_KEY             = "exercise1:values"
REPLICATION_WAIT_SEC = 2          # seconds to let async replication settle
# ────────────────────────────────────────────────────────────────────────────


def parse_args():
    p = argparse.ArgumentParser(description="Redis Enterprise Exercise 1")
    p.add_argument("--source-host",  default=DEFAULT_SOURCE_HOST)
    p.add_argument("--source-port",  type=int, default=DEFAULT_SOURCE_PORT)
    p.add_argument("--replica-host", default=DEFAULT_REPLICA_HOST)
    p.add_argument("--replica-port", type=int, default=DEFAULT_REPLICA_PORT)
    return p.parse_args()


def connect(host: str, port: int, label: str) -> redis.Redis:
    client = redis.Redis(host=host, port=port, decode_responses=True,
                         socket_connect_timeout=5)
    try:
        client.ping()
    except redis.exceptions.ConnectionError as exc:
        print(f"ERROR: Cannot reach {label} at {host}:{port} — {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Connected to {label} at {host}:{port}")
    return client


def populate_source(src: redis.Redis) -> None:
    """Delete any existing key and insert values 1-100 as a Redis List."""
    src.delete(LIST_KEY)
    # RPUSH preserves insertion order: index 0 → value 1, index 99 → value 100
    src.rpush(LIST_KEY, *range(1, 101))
    count = src.llen(LIST_KEY)
    print(f"Inserted {count} values into '{LIST_KEY}' on source-db.")


def read_reverse_from_replica(rep: redis.Redis) -> None:
    """Read the list from replica-db and print values in reverse order."""
    values = rep.lrange(LIST_KEY, 0, -1)  # returns ["1", "2", ..., "100"]
    if not values:
        print("WARNING: No data found on replica-db — replication may still be in progress.")
        return
    print(f"\nValues in reverse order from replica-db ({len(values)} entries):")
    for v in reversed(values):
        print(v)


def main():
    args = parse_args()

    src = connect(args.source_host,  args.source_port,  "source-db")
    rep = connect(args.replica_host, args.replica_port, "replica-db")

    populate_source(src)

    print(f"\nWaiting {REPLICATION_WAIT_SEC}s for async replication to propagate…")
    time.sleep(REPLICATION_WAIT_SEC)

    read_reverse_from_replica(rep)


if __name__ == "__main__":
    main()
