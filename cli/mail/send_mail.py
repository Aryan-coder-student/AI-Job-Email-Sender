#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.exceptions import AppError  # noqa: E402
from app.modules.mail.factory import build_default_mail_sender  # noqa: E402
from app.modules.mail.model import MailAttachment, MailMessage  # noqa: E402


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send a test email through the configured SMTP provider.",
    )
    parser.add_argument(
        "--to",
        action="append",
        required=True,
        help="Recipient email address. Repeat for multiple recipients.",
    )
    parser.add_argument(
        "--subject",
        required=True,
        help="Email subject line.",
    )
    parser.add_argument(
        "--body",
        required=True,
        help="Plain-text email body.",
    )
    parser.add_argument(
        "--html-body",
        default=None,
        help="Optional HTML email body.",
    )
    parser.add_argument(
        "--cc",
        action="append",
        default=[],
        help="Optional CC recipient. Repeat for multiple addresses.",
    )
    parser.add_argument(
        "--bcc",
        action="append",
        default=[],
        help="Optional BCC recipient. Repeat for multiple addresses.",
    )
    parser.add_argument(
        "--attach",
        action="append",
        type=Path,
        default=[],
        help="Optional attachment file path. Repeat for multiple files.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional path to write JSON result instead of printing to stdout.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of pretty JSON.",
    )
    return parser


def build_attachments(paths: list[Path]) -> list[MailAttachment]:
    attachments: list[MailAttachment] = []

    for path in paths:
        try:
            content = path.read_bytes()
        except OSError as error:
            raise AppError(f"Could not read attachment file {path}: {error}") from error

        attachments.append(
            MailAttachment(
                filename=path.name,
                content=content,
            )
        )

    return attachments


def write_json_output(payload: dict[str, object], output_file: Path | None, compact: bool) -> None:
    indent = None if compact else 2
    json_text = json.dumps(payload, indent=indent, ensure_ascii=False)

    if output_file:
        output_file.write_text(f"{json_text}\n", encoding="utf-8")
        return

    print(json_text)


def main(argv: Sequence[str] | None = None) -> int:
    dotenv.load_dotenv()

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        sender = build_default_mail_sender()
        result = sender.send(
            MailMessage(
                to=args.to,
                subject=args.subject,
                body_text=args.body,
                body_html=args.html_body,
                cc=args.cc,
                bcc=args.bcc,
                attachments=build_attachments(args.attach),
            )
        )
        write_json_output(result.to_dict(), args.output_file, args.compact)
    except (AppError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Unexpected Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
