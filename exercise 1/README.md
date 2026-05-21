# Redis Enterprise Exercise 1 — Building and Synchronizing Redis Databases

This project demonstrates how to set up two Redis databases, enable replication between them, load test with `memtier_benchmark`, and use a Python script to write and read data across both instances.

---

## Project Structure

```
redis/
├── docker-compose.yml       # Spins up source-db, replica-db, and RedisInsight UI
├── redis_sync.py            # Python script: inserts 1-100 into source-db, reads reversed from replica-db
├── memtier_benchmark.txt    # The memtier_benchmark command used to load test source-db
└── README.md                # This file
```

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.x
- `redis` Python library → `pip install redis`

---

## Setup

### 1. Start the databases

```bash
docker compose up -d
```

This starts three containers:

| Container | Role | Port |
|---|---|---|
| `source-db` | Primary database | `6379` |
| `replica-db` | Replica — mirrors source-db automatically | `6380` |
| `redisinsight` | Web UI to browse both databases | `5540` |

### 2. Open RedisInsight (optional)

Go to **http://localhost:5540** and add two database connections:

| Field | source-db | replica-db |
|---|---|---|
| Host | `source-db` | `replica-db` |
| Port | `6379` | `6379` |

> Use the container names as the host (not `localhost`) since RedisInsight runs inside the Docker network.

---

## Load Testing with memtier_benchmark

Run the following command to populate `source-db` with test data:

```bash
docker run --rm --network redis_default redislabs/memtier_benchmark --server=source-db --port=6379 --protocol=redis --threads=4 --clients=25 --requests=10000 --data-size=128 --key-prefix="mb:" --no-expiry --ratio=1:0
```

The exact command used is also saved in `memtier_benchmark.txt`.

---

## Running the Python Script

```bash
python redis_sync.py
```

The script will:
1. Connect to `source-db` and `replica-db`
2. Insert the values **1–100** into `source-db` as a Redis List
3. Wait 2 seconds for replication to propagate
4. Read and print the values in **reverse order** (100 → 1) from `replica-db`

### Example output

```
Connected to source-db at localhost:6379
Connected to replica-db at localhost:6380
Inserted 100 values into 'exercise1:values' on source-db.

Waiting 2s for async replication to propagate…

Values in reverse order from replica-db (100 entries):
100
99
98
...
2
1
```

### Custom endpoints

If connecting to a remote Redis Enterprise cluster instead of Docker:

```bash
python redis_sync.py \
  --source-host  your-source-db-host  --source-port  12000 \
  --replica-host your-replica-db-host --replica-port 12001
```

---

## Data Structure Discussion

### Chosen: Redis List

Values 1–100 are stored using `RPUSH exercise1:values 1 2 … 100`.  
Reverse reading is done with `LRANGE 0 -1` and Python's `reversed()`.

**Why a List?**
- Naturally ordered and sequential — a perfect fit for 1–100
- `RPUSH` preserves insertion order in a single O(N) call
- `LRANGE 0 -1` retrieves everything in one round-trip
- No extra metadata stored (unlike Sorted Sets which store a score per element)
- Simple and idiomatic Redis usage

### Alternatives considered

| Structure | Insert | Read in reverse | Trade-off |
|---|---|---|---|
| **List** *(chosen)* | `RPUSH` | `LRANGE` + `reversed()` in Python | Simplest; minimal memory |
| **Sorted Set** | `ZADD` with score = value | `ZREVRANGE` — native, no app-side sort | Best when ordering must live entirely in Redis |
| **Individual Strings** | `SET key:N value` × 100 | `SCAN` + sort in app | 100 separate keys; no inherent order; `KEYS` unsafe in production |
| **Hash** | `HSET` with field per value | `HGETALL` + sort in app | Good for named fields; no ordering |
| **Stream** | `XADD` per entry | `XREVRANGE` — native reverse | Built-in timestamps and consumer groups; overkill for simple integers |

#### When to prefer a Sorted Set

If the reversal must happen **entirely inside Redis** (e.g., inside a Lua script with no application logic), a Sorted Set with `score = value` is the better choice — `ZREVRANGE exercise1:values 0 -1` returns data pre-sorted in descending order in a single command.

#### When to prefer individual String keys

If random access to a specific value by index is frequent (e.g., "give me exactly the 42nd value"), individual String keys with `GET key:42` are O(1), whereas `LINDEX` on a List is O(N).

For this exercise — sequential insert of 1–100 with a single full-scan reverse read — the **List** offers the best simplicity-to-efficiency ratio.

---

## Stopping the Databases

```bash
docker compose down
```
