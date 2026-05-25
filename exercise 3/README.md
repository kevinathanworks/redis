# Redis Enterprise Exercise 3 — Semantic Routing

This exercise implements a semantic router using **RedisVL** that classifies incoming queries into one of three categories based on meaning — not keywords.

**RedisVL docs:** https://docs.redisvl.com/en/stable/user_guide/08_semantic_router.html

---

## Project Structure

```
exercise 3/
├── semantic_router.py   # Main script — defines routes and routes queries
├── requirements.txt     # Python dependencies
└── README.md
```

---

## Prerequisites

- Python 3.10+
- A Redis Enterprise database with **Search and Query** capability enabled
- Unauthenticated access (no password required)

Install dependencies:

```bash
pip install redisvl
```

---

## Step 1 — Create the Database

In the **Admin UI** (https://north-cluster-dot-rl-s-labs-ajqyjg.labs.ps-redis.com):

1. Create a new database:
   - **Name:** `exercise3-db`
   - **Memory:** `1 GB`
   - **Shards:** `1`
   - **Password:** *(none)*
2. Under **Capabilities**, enable **Search and Query**
3. Click **Create**

Note the endpoint (e.g. `redis-XXXXX.re-cluster1.ps-redislabs.org:XXXXX`).

---

## Step 2 — Run the Script

```bash
python semantic_router.py --redis-url redis://<host>:<port>
```

To route a single custom query:

```bash
python semantic_router.py --redis-url redis://<host>:<port> --query "Who wrote Foundation?"
```

---

## Routes Defined

| Route | What it matches |
|---|---|
| `genai_programming` | AI tools, LLMs, prompt engineering, embeddings, chatbots |
| `science_fiction` | Sci-fi movies, books, authors, space fiction |
| `classical_music` | Composers, symphonies, instruments, music theory |

Each route has 10 reference phrases. The router embeds all references as vectors in Redis and uses cosine similarity to find the closest match for an incoming query.

---

## Example Output

```
Loading router and embedding model...
Router ready.

Running test queries:

  Query : How do I integrate OpenAI into my Python app?
  Route : genai_programming

  Query : What is your favourite science fiction novel?
  Route : science_fiction

  Query : Tell me about Vivaldi's Four Seasons
  Route : classical_music
```

---

## How It Works

1. **Embedding** — each route's reference phrases are converted to vectors using a local Hugging Face model (`all-MiniLM-L6-v2`)
2. **Storage** — vectors are stored in Redis using the Search and Query index
3. **Routing** — an incoming query is embedded and compared against all stored vectors using cosine similarity
4. **Match** — the route whose references are closest (within `distance_threshold=0.55`) wins

The router runs entirely inside Redis — no external AI API calls needed at query time.

---

## Data Structure Discussion

RedisVL stores route references as **vector embeddings** in a Redis Search index (a Hash or JSON document per reference). Under the hood this uses the `HNSW` (Hierarchical Navigable Small World) algorithm for approximate nearest-neighbour search — a graph-based index optimised for high-dimensional vector lookups.

Compared to exact keyword matching:
- Handles synonyms and paraphrasing naturally
- Language-model quality matching without an external API at query time
- Sub-millisecond search at scale via HNSW
