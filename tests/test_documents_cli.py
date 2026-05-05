from __future__ import annotations

from local_ai.slices.documents.cli import build_documents_parser


def test_parser_add_source() -> None:
    args = build_documents_parser().parse_args(["add-source", "C:/archive"])
    assert args.command == "add-source"
    assert str(args.path) == "C:\\archive" or str(args.path) == "C:/archive"


def test_parser_index() -> None:
    args = build_documents_parser().parse_args(["index", "--rebuild"])
    assert args.command == "index"
    assert args.rebuild is True


def test_parser_query() -> None:
    args = build_documents_parser().parse_args(["query", "what happened"])
    assert args.command == "query"
    assert args.question == "what happened"
