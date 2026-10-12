package com.quantx.order;

import com.quantx.common.ApiResponse;
import com.quantx.order.dto.DecisionRequest;
import com.quantx.order.dto.OrderDto;
import com.quantx.order.dto.SubmitOrderRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 주문 결재 API. 네 개 모두 Senior Manager만 부를 수 있다.
 * <p>
 * Junior도, AI Agent도 여기 닿지 못한다. Agent에게는 이 서버를 부를 자격 증명 자체가 없다.
 */
@RestController
@RequestMapping("/api/orders")
@RequiredArgsConstructor
public class OrderController {

	private final OrderApprovalService service;

	@PostMapping
	@ResponseStatus(HttpStatus.CREATED)
	@PreAuthorize("hasRole('SENIOR_MANAGER')")
	public ApiResponse<OrderDto> submit(
		@AuthenticationPrincipal String userId,
		@Valid @RequestBody SubmitOrderRequest req) {
		return ApiResponse.success(service.submit(userId, req));
	}

	@GetMapping("/pending")
	@PreAuthorize("hasRole('SENIOR_MANAGER')")
	public ApiResponse<List<OrderDto>> pending() {
		return ApiResponse.success(service.listPending());
	}

	@PostMapping("/{orderId}/approve")
	@PreAuthorize("hasRole('SENIOR_MANAGER')")
	public ApiResponse<OrderDto> approve(
		@AuthenticationPrincipal String userId,
		@PathVariable String orderId,
		@RequestBody(required = false) DecisionRequest req) {
		String comment = req == null ? null : req.comment();
		return ApiResponse.success(service.approve(userId, orderId, comment));
	}

	@PostMapping("/{orderId}/reject")
	@PreAuthorize("hasRole('SENIOR_MANAGER')")
	public ApiResponse<OrderDto> reject(
		@AuthenticationPrincipal String userId,
		@PathVariable String orderId,
		@RequestBody(required = false) DecisionRequest req) {
		String reason = req == null ? null : req.reason();
		return ApiResponse.success(service.reject(userId, orderId, reason));
	}
}