from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
import csv
import json
import re
from typing import Iterable

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


SUPPORTED_EXTENSIONS = {".txt", ".md", ".rst", ".csv", ".json", ".html", ".htm", ".pdf"}


@dataclass(frozen=True)
class DocumentHit:
    path: Path
    score: int
    excerpt: str


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def text(self) -> str:
        return " ".join(self.parts)


def _safe_read_text(path: Path) -> str:
    encodings = ("utf-8", "utf-16", "latin-1")
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding, errors="ignore")
        except UnicodeError:
            continue
        except OSError:
            continue
    return ""


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".rst"}:
        return _safe_read_text(path)
    if suffix == ".csv":
        rows: list[str] = []
        try:
            with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    rows.append(" | ".join(cell.strip() for cell in row if cell.strip()))
        except OSError:
            return ""
        return "\n".join(rows)
    if suffix == ".json":
        try:
            raw = _safe_read_text(path)
            data = json.loads(raw)
        except Exception:
            return _safe_read_text(path)
        return json.dumps(data, ensure_ascii=False, indent=2)
    if suffix in {".html", ".htm"}:
        parser = _TextExtractor()
        parser.feed(_safe_read_text(path))
        return parser.text()
    if suffix == ".pdf":
        if PdfReader is None:
            return ""
        try:
            reader = PdfReader(str(path))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            return "\n".join(pages)
        except Exception:
            return ""
    return ""


def iter_documents(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def search_documents(root: Path, query: str, limit: int = 10, max_chars: int = 6000) -> list[DocumentHit]:
    terms = [term for term in re.split(r"\s+", query.lower().strip()) if term]
    results: list[DocumentHit] = []

    for path in iter_documents(root):
        haystack_name = path.name.lower()
        score = sum(5 for term in terms if term in haystack_name)

        text = extract_text(path)
        if not text:
            if score > 0:
                results.append(DocumentHit(path=path, score=score, excerpt=""))
            continue

        lowered = text.lower()
        for term in terms:
            score += lowered.count(term)

        if score > 0:
            first_match = next((term for term in terms if term in lowered), None)
            if first_match:
                idx = lowered.find(first_match)
                start = max(0, idx - 220)
                end = min(len(text), idx + max_chars)
                excerpt = text[start:end].strip()
            else:
                excerpt = text[:max_chars].strip()
            results.append(DocumentHit(path=path, score=score, excerpt=excerpt))

    results.sort(key=lambda item: (item.score, item.path.name.lower()), reverse=True)
    return results[:limit]


def recent_documents(root: Path, limit: int = 5) -> list[Path]:
    docs = [path for path in iter_documents(root)]
    docs.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return docs[:limit]


def build_source_bundle(root: Path, query: str, limit: int = 5) -> str:
    hits = search_documents(root, query=query, limit=limit)
    if not hits:
        fallback_docs = recent_documents(root, limit=limit)
        if not fallback_docs:
            return "Nenhum documento relevante foi encontrado."
        chunks: list[str] = []
        for path in fallback_docs:
            text = extract_text(path)
            excerpt = text[:6000].strip() if text else ""
            chunks.append(f"ARQUIVO: {path}\nTRECHO:\n{excerpt}\n")
        return "\n".join(chunks)

    chunks: list[str] = []
    for hit in hits:
        chunks.append(f"ARQUIVO: {hit.path}\nTRECHO:\n{hit.excerpt}\n")
    return "\n".join(chunks)
