package com.quantx.core;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.quantx.common.ApiException;
import com.quantx.common.ErrorCode;
import com.quantx.core.dto.CoreOrderDto;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Core Zone에 시스템 권한으로 쓰는 클라이언트. 결재를 마친 뒤에만 불린다.
 * <p>
 * 접수·승인·반려 세 가지뿐이다. 사용자 요청을 그대로 흘려보내는 통로가 아니라,
 * 결재 결과를 원장에 반영하는 좁은 창구여야 한다.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class MockCoreSystemClient {

	private final WebClient mockCoreWebClient;
	private final ObjectMapper objectMapper = new ObjectMapper();

	public CoreOrderDto submitOrder(String accountId, String ticker, String side,
		int quantity, int price, String submittedBy,
		Long researchReportId, String idempotencyKey) {
		Map<String, Object> body = new LinkedHashMap<>();
		body.put("accountId", accountId);
		body.put("ticker", ticker);
		body.put("side", side);
		body.put("quantity", quantity);
		body.put("price", price);
		body.put("submittedBy", submittedBy);
		body.put("researchReportId", researchReportId);

		return call(mockCoreWebClient.post()
			.uri("/core/orders")
			.header("X-Idempotency-Key", idempotencyKey)
			.header("X-User-Id", submittedBy)
			.bodyValue(body));
	}

	public CoreOrderDto approveOrder(String orderId, String decidedBy, String comment) {
		return call(mockCoreWebClient.post()
			.uri("/core/orders/{orderId}/approve", orderId)
			.header("X-User-Id", decidedBy)
			.bodyValue(Map.of("decidedBy", decidedBy,
				"comment", comment == null ? "" : comment)));
	}

	public CoreOrderDto rejectOrder(String orderId, String decidedBy, String reason) {
		return call(mockCoreWebClient.post()
			.uri("/core/orders/{orderId}/reject", orderId)
			.header("X-User-Id", decidedBy)
			.bodyValue(Map.of("decidedBy", decidedBy,
				"reason", reason == null ? "" : reason)));
	}

	private CoreOrderDto call(WebClient.RequestHeadersSpec<?> spec) {
		try {
			return spec.retrieve()
				.bodyToMono(CoreOrderDto.class)
				// Mock Core는 일부러 503을 내기도 한다. 두 번까지는 다시 시도한다
				.retryWhen(Retry.backoff(2, Duration.ofMillis(500))
					.filter(this::isRetryable))
				.block();
		} catch (WebClientResponseException.Conflict e) {
			// 한도 초과·중복·상태 전이 위반. 사용자에게 이유를 그대로 보여 준다
			throw new ApiException(ErrorCode.CORE_ORDER_REJECTED,
				"Core Zone이 주문을 거절했다", parseError(e));
		} catch (WebClientResponseException.Forbidden e) {
			// 여기가 뜨면 시스템 키 설정이 틀린 것이다
			log.error("Core Zone 인증 실패. X-System-Key를 확인해야 한다");
			throw new ApiException(ErrorCode.CORE_UNAVAILABLE, "Core Zone 인증 실패");
		} catch (WebClientResponseException.NotFound e) {
			throw new ApiException(ErrorCode.NOT_FOUND, "주문을 찾지 못했다");
		} catch (Exception e) {
			log.error("Core Zone 호출 실패", e);
			throw new ApiException(ErrorCode.CORE_UNAVAILABLE, "Core Zone 응답 없음");
		}
	}

	private boolean isRetryable(Throwable t) {
		if (t instanceof WebClientResponseException.ServiceUnavailable) {
			log.warn("Core Zone 503. 다시 시도한다");
			return true;
		}
		return t instanceof WebClientRequestException;
	}

	private Object parseError(WebClientResponseException e) {
		try {
			JsonNode node = objectMapper.readTree(e.getResponseBodyAsString());
			return objectMapper.convertValue(node.path("detail"), Object.class);
		} catch (Exception ignored) {
			return e.getResponseBodyAsString();
		}
	}
}