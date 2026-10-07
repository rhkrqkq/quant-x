import re
from typing import List, Set


CITATION_RE = re.compile(r"\[([\w\-./#]+#chunk-\d+)\]")


def extract_citations(text: str) -> List[str]:
    """답변 본문에서 [chunk_id] 패턴을 추출하여 중복 제거."""
    found: List[str] = []
    seen: Set[str] = set()
    for m in CITATION_RE.finditer(text):
        cid = m.group(1)
        if cid not in seen:
            seen.add(cid)
            found.append(cid)
    return found


def validate_citations(cited: List[str], available: List[str]) -> tuple[List[str], List[str]]:
    """LLM이 인용한 chunk_id 중 실제 검색 결과에 존재하는 것만 valid.
    반환: (valid, invalid)
    """
    available_set = set(available)
    valid = [c for c in cited if c in available_set]
    invalid = [c for c in cited if c not in available_set]
    return valid, invalid