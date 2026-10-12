package com.quantx.order.dto;

import jakarta.validation.constraints.*;

public record SubmitOrderRequest(
	Long reportId,                                   // 어느 보고서를 근거로 냈는지 (선택)

	@NotBlank @Size(max = 32)
	String accountId,

	@NotBlank @Size(max = 16)
	String ticker,

	@NotNull @Pattern(regexp = "BUY|SELL")
	String side,

	@NotNull @Positive
	Integer quantity,

	@NotNull @Positive
	Integer price
) {}