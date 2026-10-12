package com.quantx.core.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

/** Mock Core Service가 돌려주는 주문 한 건. */
@JsonIgnoreProperties(ignoreUnknown = true) // 역직렬화시 존재하지 않는 속성 예외 방지
public record CoreOrderDto(
	String orderId,
	String accountId,
	String ticker,
	String side,
	Integer quantity,
	Integer price,
	Long estimatedAmountKrw,
	String status,
	String submittedBy,
	Long researchReportId,
	String decidedBy,
	String decidedAt,
	String executedAt,
	Long executionPriceKrw,
	Long actualAmountKrw,
	String rejectReason,
	String createdAt,
	String decisionRequiredBy,
	boolean duplicate
) {}