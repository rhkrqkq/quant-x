"""PII 정규식과 Prompt Injection 패턴. 부록 A §4.2 · §5.1을 코드로 옮긴 것이다.

[보안] 규칙 기반이라 우회가 가능하다. "주민번호 900101 다시 1234567" 처럼 끊어 쓰면
       아래 정규식은 잡지 못한다. 그래서 이것만으로 안전하다고 말하면 안 되고,
       Tool Gateway의 Scope 검사·Core Zone의 키 분리 같은 다른 겹이 함께 있어야 한다.
       한국어 NER을 붙이면 재현율이 올라가지만 모델 의존성이 생겨 본 과정에서는 두지 않는다.
"""
from __future__ import annotations
import re
from typing import List, Optional, Pattern, Tuple

# 계좌번호 패턴이 삼키는 것 중 계좌가 아닌 것들.
# `2026-07-31`은 4-2-2 자리라 계좌 정규식에 그대로 걸린다. 예외를 안 두면
# 날짜가 들어간 정상 질문이 전부 차단된다 — 실습에서 바로 부딪히는 오탐이다.
_DATE_LIKE = re.compile(r"^(19|20)\d{2}-\d{2}-\d{2}$")

# (코드, 정규식, 마스킹 태그, 예외 패턴)
PII_PATTERNS: List[Tuple[str, Pattern[str], str, Optional[Pattern[str]]]] = [
    # 주민등록번호. 뒷자리 첫 글자는 1~4만 본다 (외국인등록번호 5~8은 별도 규칙이 필요하다)
    ("RRN", re.compile(r"\d{6}-?[1-4]\d{6}"), "[RRN_MASKED]", None),
    # 카드번호를 계좌번호보다 먼저 본다. 4-4-4-4는 계좌 패턴에도 걸리기 때문이다
    ("CARD", re.compile(r"\d{4}-\d{4}-\d{4}-\d{4}"), "[CARD_MASKED]", None),
    ("PHONE", re.compile(r"01[016789]-?\d{3,4}-?\d{4}"), "[PHONE_MASKED]", None),
    ("BIZ", re.compile(r"\d{3}-\d{2}-\d{5}"), "[BIZ_MASKED]", None),
    ("ACCT", re.compile(r"\d{2,6}-\d{2,6}-\d{2,6}"), "[ACCT_MASKED]", _DATE_LIKE),
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL_MASKED]", None),
]

# [주의] 순서가 결과를 바꾼다. ACCT(2~6-2~6-2~6)가 CARD·PHONE·BIZ를 삼키므로 뒤에 둔다.
#        위에서부터 차례로 치환하고, 앞선 규칙이 남긴 [XXX_MASKED]는 숫자가 아니라 다시 안 걸린다.
#
# 예외를 둔다는 건 구멍을 낸다는 뜻이기도 하다. `2026-07-31` 모양으로 만든 계좌번호는
# 이제 통과한다. 재현율과 오탐은 맞바꾸는 관계이고, 규칙 기반 필터의 한계가 여기다.

# Prompt Injection. 문장이 아니라 '의도'를 잡는 패턴이라 오탐이 난다.
# 그래서 BLOCKED가 아니라 WARNING으로 두는 항목도 있다 (input_filter가 판정한다).
INJECTION_PATTERNS: List[Tuple[str, Pattern[str], str]] = [
    ("IGNORE_PREV",
     re.compile(r"(이전|위의|앞의|모든)[^.\n]{0,10}(지시|명령|규칙|프롬프트)[^.\n]{0,10}"
                r"(무시|잊|해제)|ignore\s+(all\s+)?(previous|prior|above)", re.I),
     "이전 지시를 무시하라는 요구"),
    ("REVEAL_PROMPT",
     re.compile(r"(시스템\s*프롬프트|system\s*prompt|너의?\s*(지시문|규칙|설정))[^.\n]{0,15}"
                r"(보여|알려|출력|공개|말해)|reveal\s+your\s+(prompt|instructions)", re.I),
     "시스템 프롬프트를 요구"),
    ("ROLE_CHANGE",
     re.compile(r"(너는|당신은|지금부터)[^.\n]{0,20}(개발자|관리자|admin|DAN)[^.\n]{0,10}(이다|야|입니다|처럼)"
                r"|act\s+as\s+(a\s+)?(developer|admin|root)", re.I),
     "역할을 바꾸라는 요구"),
    ("TOOL_ABUSE",
     re.compile(r"(주문|매수|매도|이체|송금)[^.\n]{0,15}(넣어|실행|해\s*줘|처리해|진행해)"),
     "Agent에게 직접 거래를 시키려는 요구"),
    ("SYSTEM_TAG",
     re.compile(r"</?(system|assistant|im_start|im_end)\b", re.I),
     "대화 역할 태그를 흉내낸 문자열"),
]

# 차단까지 가는 Injection 코드. 나머지는 경고만 남기고 통과시킨다.
BLOCKING_INJECTION_CODES = {"IGNORE_PREV", "REVEAL_PROMPT", "SYSTEM_TAG"}