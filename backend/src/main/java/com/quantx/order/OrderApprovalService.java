package com.quantx.order;

import com.quantx.common.ApiException;
import com.quantx.common.ErrorCode;
import com.quantx.core.MockCoreSystemClient;
import com.quantx.core.dto.CoreOrderDto;
import com.quantx.order.dto.OrderDto;
import com.quantx.order.dto.SubmitOrderRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

/**
 * HITL 결재. 주문은 여기서 두 번 사람 손을 탄다 — 낼 때 한 번, 승인할 때 한 번.
 * <p>
 * AI Agent는 이 서비스를 부를 수 없다. 호출자는 JWT를 들고 온 사람뿐이다.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class OrderApprovalService {

	private final MockCoreSystemClient mockCore;
	private final OrderApprovalQueueRepository queue;

	@Transactional
	public OrderDto submit(String userId, SubmitOrderRequest req) {
		// 멱등성 키는 서버가 만든다. 클라이언트가 보내게 하면 재전송 때 새 키가 오기 쉽다
		String idempotencyKey = UUID.randomUUID().toString();

		CoreOrderDto order = mockCore.submitOrder(
			req.accountId(), req.ticker(), req.side(), req.quantity(), req.price(),
			userId, req.reportId(), idempotencyKey);

		OrderApprovalQueue saved = queue.save(OrderApprovalQueue.builder()
			.orderId(order.orderId())
			.researchReportId(req.reportId())
			.accountId(order.accountId())
			.ticker(order.ticker())
			.side(order.side())
			.quantity(order.quantity())
			.price(order.price())
			.estimatedAmountKrw(order.estimatedAmountKrw())
			.submittedBy(userId)
			.status(order.status())
			.build());

		// 9장에서 audit_log 테이블 기록으로 바뀐다. 지금은 로그로만 남긴다
		log.info("CORE_ORDER_SUBMITTED user={} order={} ticker={} amount={}",
			userId, order.orderId(), order.ticker(), order.estimatedAmountKrw());
		return OrderDto.from(saved);
	}

	@Transactional
	public OrderDto approve(String userId, String orderId, String comment) {
		OrderApprovalQueue row = find(orderId);
		CoreOrderDto order = mockCore.approveOrder(orderId, userId, comment);

		row.applyDecision(order.status(), userId, comment);
		log.info("CORE_ORDER_EXECUTED user={} order={} amount={}",
			userId, orderId, order.actualAmountKrw());
		return OrderDto.from(row);
	}

	@Transactional
	public OrderDto reject(String userId, String orderId, String reason) {
		OrderApprovalQueue row = find(orderId);
		CoreOrderDto order = mockCore.rejectOrder(orderId, userId, reason);

		row.applyDecision(order.status(), userId, reason);
		log.info("CORE_ORDER_REJECTED user={} order={} reason={}", userId, orderId, reason);
		return OrderDto.from(row);
	}

	@Transactional(readOnly = true)
	public List<OrderDto> listPending() {
		return queue.findByStatusOrderByCreatedAtAsc("PENDING").stream()
			.map(OrderDto::from)
			.toList();
	}

	private OrderApprovalQueue find(String orderId) {
		return queue.findByOrderId(orderId)
			.orElseThrow(() -> new ApiException(ErrorCode.NOT_FOUND, "결재 건을 찾지 못했다"));
	}
}