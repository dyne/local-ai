from __future__ import annotations

import argparse
import json
from pathlib import Path

from local_ai.slices.documents.request import AddSourceRequest, IndexSourceRequest, QueryDocumentsRequest
from local_ai.slices.documents.service_bundle import build_documents_service_bundle


def build_documents_parser() -> argparse.ArgumentParser:
    """Build CLI parser for documents slice operations."""

    parser = argparse.ArgumentParser(description="Local AI Documents CLI.")
    sub = parser.add_subparsers(dest="command", required=True)

    add_source = sub.add_parser("add-source", help="Register one source path.")
    add_source.add_argument("path", type=Path)
    add_source.add_argument("--label", default=None)

    index = sub.add_parser("index", help="Run Recoll indexing for registered sources.")
    index.add_argument("--rebuild", action="store_true")

    query = sub.add_parser("query", help="Query indexed documents.")
    query.add_argument("question")
    query.add_argument("--max-documents", type=int, default=20)
    query.add_argument("--max-passages", type=int, default=8)

    return parser


def run_documents_cli(argv: list[str] | None = None) -> int:
    """Execute documents CLI commands."""

    args = build_documents_parser().parse_args(argv)
    bundle = build_documents_service_bundle()
    if args.command == "add-source":
        response = bundle.add_source_service.execute(
            AddSourceRequest(path=str(args.path), label=args.label),
        )
    elif args.command == "index":
        response = bundle.index_documents_service.execute(IndexSourceRequest(rebuild=bool(args.rebuild)))
    else:
        response = bundle.query_documents_service.execute(
            QueryDocumentsRequest(
                query=args.question,
                max_documents=int(args.max_documents),
                max_passages=int(args.max_passages),
            )
        )
    print(json.dumps(response.to_dict(), default=str, indent=2))
    status = getattr(response, "status", "")
    return 0 if status in {"ok", "success"} else 1
