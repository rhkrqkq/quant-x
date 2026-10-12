package com.quantx.order.dto;

import com.quantx.order.OrderApprovalQueue;

import java.time.LocalDateTime;

public record OrderDto(
	String orderId,
	Long researchReportId,
	String accountId,
	String ticker,
	String side,
	Integer quantity,
	Integer price,
	Long estimatedAmountKrw,
	String status,
	String submittedBy,
	String decidedBy,
	LocalDateTime decidedAt,
	String comment,
	LocalDateTime createdAt
) {
	public static OrderDto from(OrderApprovalQueue q) {
		return new OrderDto(
			q.getOrderId(), q.getResearchReportId(), q.getAccountId(),
			q.getTicker(), q.getSide(), q.getQuantity(), q.getPrice(),
			q.getEstimatedAmountKrw(), q.getStatus(), q.getSubmittedBy(),
			q.getDecidedBy(), q.getDecidedAt(), q.getComment(), q.getCreatedAt());
	}
}