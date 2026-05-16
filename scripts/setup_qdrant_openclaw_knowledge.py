#!/usr/bin/env python3
"""
Safe setup helper for the openclaw_knowledge Qdrant collection.

Default behavior is check-only:
- connects to Qdrant
- lists collections
- reports whether openclaw_knowledge exists
- does not ingest data
- does not delete or modify existing collections
- does not modify pdf_embeddings

Collection creation only occurs when this script is run manually with --create.
"""

import argparse
import os
import sys

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
except ImportError as exc:
    print(f"qdrant-client unavailable: {exc}")
    sys.exit(1)

COLLECTION_NAME = "openclaw_knowledge"
DEFAULT_URL = "http://localhost:6333"
DEFAULT_VECTOR_SIZE = 1536


def build_client(url: str, api_key: str | None) -> QdrantClient:
    kwargs = {"url": url}
    if api_key:
        kwargs["api_key"] = api_key
    return QdrantClient(**kwargs)


def collection_names(client: QdrantClient) -> list[str]:
    collections = client.get_collections().collections
    return [collection.name for collection in collections]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check or create the openclaw_knowledge Qdrant collection safely."
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("QDRANT_URL", DEFAULT_URL),
        help="Qdrant URL. Default: http://localhost:6333",
    )
    parser.add_argument(
        "--api-key-env",
        default="QDRANT_API_KEY",
        help="Environment variable containing the Qdrant API key, if any.",
    )
    parser.add_argument(
        "--vector-size",
        type=int,
        default=int(os.environ.get("QDRANT_VECTOR_SIZE", DEFAULT_VECTOR_SIZE)),
        help="Vector size for a new collection. Default: 1536.",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create openclaw_knowledge if missing. No data is ingested.",
    )
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    client = build_client(args.url, api_key)
    names = collection_names(client)

    if COLLECTION_NAME in names:
        print(f"{COLLECTION_NAME} collection exists. No action taken.")
        return 0

    if not args.create:
        print("openclaw_knowledge collection missing. User approval required to create.")
        return 2

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=args.vector_size, distance=Distance.COSINE),
    )
    print(f"{COLLECTION_NAME} collection created. No data ingested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
