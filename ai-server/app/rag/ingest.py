"""사용 예:
python -m app.rag.ingest --hf nmixx-fin/synthetic_financial_report_korean --limit 100
python -m app.rag.ingest --pdf ./samples/금융권-ai-보안가이드.pdf
"""
from __future__ import annotations

# === .env 자동 로드 (CLI 실행 시 OS 환경변수가 없어도 .env에서 읽음) ===
from dotenv import load_dotenv
load_dotenv()

import argparse
import logging
from pathlib import Path

from .loaders import load_huggingface_dataset, load_local_pdf, load_local_markdown
from .splitter import split_documents
from .service import RAGService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--hf", type=str, default=None, help="HuggingFace dataset name")
    p.add_argument("--limit", type=int, default=200)
    p.add_argument("--pdf", type=str, default=None)
    p.add_argument("--md", type=str, default=None)
    p.add_argument("--reset", action="store_true", help="reset collection first")
    args = p.parse_args()

    svc = RAGService()
    if args.reset:
        svc.store.reset()

    docs = []
    if args.hf:
        docs.extend(list(load_huggingface_dataset(args.hf, limit=args.limit)))
    if args.pdf:
        docs.extend(load_local_pdf(Path(args.pdf)))
    if args.md:
        docs.extend(load_local_markdown(Path(args.md)))

    if not docs:
        raise SystemExit("--hf, --pdf, --md 중 하나는 지정해야 합니다")

    chunks = split_documents(docs)
    ids = svc.ingest(chunks)
    print(f"✅ {len(ids)} chunks ingested")


if __name__ == "__main__":
    main()