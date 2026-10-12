"""Core Zone(Mock Core Service) 호출 클라이언트. 8장에서 추가.

**Read 메서드만 둔다.** 주문을 넣는 메서드는 아예 만들지 않는다.
있으면 언젠가 불린다 — 프롬프트로 "쓰지 마라"라고 부탁하는 것과, 코드에 없어서 못 부르는 것은 다르다.
"""
from __future__ import annotations
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class MockCoreClient:
    def __init__(self, base_url: str, api_key: str,
                 max_retries: int = 1, timeout: float = 10.0) -> None:
        self.max_retries = max_retries
        # 연결을 재사용한다. 매번 새로 열면 첫 호출마다 이름 해석과 TCP 연결 비용을 다시 낸다.
        # 윈도우에서 localhost가 IPv6로 먼저 잡히면 그 비용이 초 단위로 튄다
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={
                "X-Internal-API-Key": api_key,
                "X-Caller": "ai-server",      # Mock Core의 감사 로그에 남는다
            },
        )

    # ---------- Read Tool 3종 ----------
    def get_account(self, account_id: str) -> Dict[str, Any]:
        """가상 계좌 정보. 계좌번호와 이름은 Core Zone에서 이미 마스킹돼 나온다."""
        return self._get(f"/core/accounts/{account_id}")

    def get_balance(self, account_id: str) -> Dict[str, Any]:
        """잔고와 주문 가능 금액."""
        return self._get(f"/core/accounts/{account_id}/balance")

    def list_orders(self, account_id: str,
                    status: Optional[str] = None) -> List[Dict[str, Any]]:
        """주문 내역. 접수·결재는 여기서 할 수 없고 조회만 된다."""
        params: Dict[str, Any] = {"account_id": account_id}
        if status:
            params["status"] = status
        return self._get("/core/orders", params=params).get("items", [])

    # ---------- 내부 ----------
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                resp = self._client.get(path, params=params)
                # 503은 Mock Core가 일부러 내는 경우가 있다. 한 번은 다시 시도해 본다
                if resp.status_code == 503 and attempt < self.max_retries:
                    wait = 0.5 * (2 ** attempt)
                    logger.warning("Core Zone 503. %.1f초 뒤 재시도 (%d/%d)",
                                   wait, attempt + 1, self.max_retries)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                # 403·404는 다시 불러도 같다. 바로 올린다
                raise RuntimeError(
                    f"Core Zone 호출 실패 {e.response.status_code}: {e.response.text[:200]}"
                ) from e
            except httpx.RequestError as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(0.5 * (2 ** attempt))
                    continue

        raise RuntimeError(f"Core Zone에 닿지 못했다: {last_error}")


# 전역 인스턴스. registry가 이 객체의 메서드를 Tool로 등록한다
mock_core_client = MockCoreClient(
    base_url=settings.mock_core_base_url,
    api_key=settings.mock_core_api_key,
)