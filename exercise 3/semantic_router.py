#!/usr/bin/env python3
import argparse
import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from redisvl.extensions.router import Route, SemanticRouter
from redisvl.utils.vectorize import HFTextVectorizer

# ── Route definitions ────────────────────────────────────────────────────────

genai_programming = Route(
    name="genai_programming",
    references=[
        "How do I use the ChatGPT API?",
        "What is prompt engineering?",
        "Explain large language models",
        "How do transformer architectures work?",
        "What is retrieval augmented generation?",
        "How do I fine-tune a machine learning model?",
        "Tell me about generative AI tools for developers",
        "What is the difference between GPT-3 and GPT-4?",
        "How do I build a chatbot with AI?",
        "Explain embeddings and vector databases",
    ],
    distance_threshold=0.7,
)

science_fiction = Route(
    name="science_fiction",
    references=[
        "What are the best sci-fi movies?",
        "Tell me about the Star Wars universe",
        "Who wrote the Dune novels?",
        "Recommend a science fiction book",
        "What is the plot of The Matrix?",
        "Tell me about Isaac Asimov's robots",
        "What are the best sci-fi TV series?",
        "Explain the storyline of Interstellar",
        "Who is the author of Foundation series?",
        "What makes a good science fiction story?",
    ],
    distance_threshold=0.7,
)

classical_music = Route(
    name="classical_music",
    references=[
        "Who composed Beethoven's 9th Symphony?",
        "Tell me about Mozart's life",
        "What is a sonata?",
        "Recommend classical music for studying",
        "Who is Johann Sebastian Bach?",
        "What is the difference between baroque and classical music?",
        "Tell me about Chopin's nocturnes",
        "What is an orchestra?",
        "Who are the most famous classical composers?",
        "Explain the structure of a symphony",
    ],
    distance_threshold=0.7,
)

# ────────────────────────────────────────────────────────────────────────────

ROUTES = [genai_programming, science_fiction, classical_music]

TEST_QUERIES = [
    "How do I integrate OpenAI into my Python app?",
    "What is your favourite science fiction novel?",
    "Tell me about Vivaldi's Four Seasons",
]


def build_router(redis_url: str) -> SemanticRouter:
    return SemanticRouter(
        name="exercise3-router",
        vectorizer=HFTextVectorizer(),
        routes=ROUTES,
        redis_url=redis_url,
        overwrite=True,
    )


def route_query(router: SemanticRouter, query: str) -> None:
    match = router(query)
    if match and match.name:
        print(match.name)
    else:
        print("no_match")


def main():
    parser = argparse.ArgumentParser(description="Redis Semantic Router — Exercise 3")
    parser.add_argument("--redis-url", required=True,
                        help="Redis connection URL e.g. redis://host:port")
    parser.add_argument("--query", default=None,
                        help="Single query to route (optional — runs test queries if omitted)")
    args = parser.parse_args()

    print("Loading router and embedding model...")
    router = build_router(args.redis_url)
    print("Router ready.\n")

    if args.query:
        route_query(router, args.query)
    else:
        print("Running test queries:\n")
        for q in TEST_QUERIES:
            match = router(q)
            matched = match.name if match and match.name else "no_match"
            print(f"  Query : {q}")
            print(f"  Route : {matched}\n")


if __name__ == "__main__":
    main()
