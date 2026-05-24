# Redis Enterprise Exercise 1 — Building and Synchronizing Redis Databases

## Project Structure

```
exercise 1/
├── redis_sync.py          # Inserts 1-100 into source-db, reads reversed from replica-db
├── memtier_benchmark.txt  # memtier_benchmark command run on the load node
├── docker-compose.yml     # Local dev only
└── README.md
```

---

## Prerequisites

- Python 3.x
- `pip install redis`
- Access to the Redis Enterprise cluster

---

## Step 1 — Create source-db

In the **Admin UI**, create a new Redis database:
- **Name:** `source-db`
- **Memory:** `2 GB`
- **Shards:** `1`
- **Password:** *(none)*

Note the endpoint after creation (e.g. `redis-12000.re-cluster1.ps-redislabs.org:12000`).

---

## Step 2 — Create replica-db with Replica Of

Create a second database:
- **Name:** `replica-db`
- **Memory:** `2 GB`
- **Shards:** `1`
- **Password:** *(none)*

Enable **Replica Of** and set the source URI to the `source-db` endpoint before activating.

---

## Step 3 — Run memtier_benchmark on the Load Node

SSH into the load node via the bastion and run the command in `memtier_benchmark.txt`, replacing the host and port with your `source-db` endpoint.

Save the command on the load node:

```bash
cat > /tmp/memtier_benchmark.txt << 'EOF'
memtier_benchmark --server=<source-db-host> --port=<source-db-port> --protocol=redis --threads=4 --clients=25 --requests=10000 --data-size=128 --key-prefix="mb:" --ratio=1:0 --pipeline=10 --run-count=1 --hide-histogram
EOF
```

---

## Step 4 — Run the Python Script

```bash
python redis_sync.py \
  --source-host  <source-db-host>  --source-port  <source-db-port> \
  --replica-host <replica-db-host> --replica-port <replica-db-port>
```

### Example output

```
Connected to source-db  at redis-10903.re-cluster1.ps-redislabs.org:10903
Connected to replica-db at redis-17117.re-cluster1.ps-redislabs.org:17117
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

---

## Data Structure Discussion

### Chosen: Redis List

Values 1–100 are stored with `RPUSH exercise1:values 1 2 … 100` and read back with `LRANGE 0 -1`, reversed in Python.

**Why a List?**
- Preserves insertion order natively — no extra metadata needed
- Single `RPUSH` call, single `LRANGE` call — two round-trips total
- Reversal with Python's `reversed()` costs nothing for 100 elements

### Alternatives considered

| Structure | Insert | Read reversed | Trade-off |
|---|---|---|---|
| **List** *(chosen)* | `RPUSH` | `LRANGE` + `reversed()` in Python | Simplest; minimal memory |
| **Sorted Set** | `ZADD` with score = value | `ZREVRANGE` — native | Best if ordering must stay inside Redis |
| **Individual Strings** | `SET key:N` × 100 | `SCAN` + sort in app | No inherent order; `KEYS` unsafe in production |
| **Hash** | `HSET` | `HGETALL` + sort in app | Good for named fields; no ordering |
| **Stream** | `XADD` | `XREVRANGE` — native | Overkill for plain integers |
