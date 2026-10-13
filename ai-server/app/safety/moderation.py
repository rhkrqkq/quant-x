"""Moderation 연동. 기본은 꺼져 있다.

외부 Moderation API는 두 가지 이유로 기본값이 off다.
① 10장에서 폐쇄망 모드(`ALLOW_EXTERNAL_LLM=false`)를 켜면 나갈 수 없는 호출이다.
   내부망 금융 시스템에서 사용자 입력을 외부 API로 보내는 것 자체가 심사 대상이 된다.
② 실습 중 네트워크 사정으로 실패하면 어디까지가 내 코드 문제인지 알 수 없다.

그래도 인터페이스는 만들어 둔다. 규칙 기반 필터가 못 잡는 것을 모델이 잡는 자리가
어디인지 코드에 표시해 두는 편이, 나중에 붙일 때 구조를 다시 짜는 것보다 낫다.
"""
from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Dict, Optional

from ..config import settings

logger = logging.getLogger(__name__)


class ModerationChecker(ABC):
    @abstractmethod
    def check(self, text: str) -> Optional[Dict[str, Any]]:
        """판정 결과. 꺼져 있으면 None을 돌려준다 (응답의 moderation이 null이 된다)."""


class NullModerationChecker(ModerationChecker):
    """기본 구현. 아무것도 하지 않는다."""

    def check(self, text: str) -> Optional[Dict[str, Any]]:
        return None


class OpenAIModerationChecker(ModerationChecker):
    """omni-moderation-latest 호출. ENABLE_MODERATION=true일 때만 쓰인다."""

    def check(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.moderations.create(
                model="omni-moderation-latest", input=text[:4000])
            r = resp.results[0]
            return {
                "flagged": r.flagged,
                "categories": [k for k, v in r.categories.model_dump().items() if v],
            }
        except Exception:
            # [주의] Moderation 실패로 정상 요청을 막지 않는다. 못 봤다는 사실만 남긴다.
            #        여기서 fail-closed로 가면 외부 API 장애가 곧 서비스 중단이 된다
            logger.exception("Moderation 호출 실패. 판정 없이 진행한다")
            return {"flagged": False, "categories": [], "error": "moderation_unavailable"}


@lru_cache(maxsize=1)
def get_moderation_checker() -> ModerationChecker:
    if settings.enable_moderation and settings.allow_external_llm:
        logger.info("Moderation 사용: OpenAI")
        return OpenAIModerationChecker()
    return NullModerationChecker()