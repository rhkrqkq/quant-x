package com.quantx.common;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;

@Getter
@RequiredArgsConstructor
public enum ErrorCode {
    UNAUTHORIZED(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED"),
    FORBIDDEN(HttpStatus.FORBIDDEN, "FORBIDDEN"),
    NOT_FOUND(HttpStatus.NOT_FOUND, "NOT_FOUND"),
    VALIDATION_ERROR(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR"),
    GUARDRAIL_BLOCKED(HttpStatus.UNPROCESSABLE_ENTITY, "GUARDRAIL_BLOCKED"),
    KILL_SWITCH_ACTIVE(HttpStatus.SERVICE_UNAVAILABLE, "KILL_SWITCH_ACTIVE"),
    LLM_PROVIDER_ERROR(HttpStatus.BAD_GATEWAY, "LLM_PROVIDER_ERROR"),
    RATE_LIMIT_EXCEEDED(HttpStatus.TOO_MANY_REQUESTS, "RATE_LIMIT_EXCEEDED"),
    INTERNAL_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR"),
    AI_SERVER_UNAVAILABLE(HttpStatus.SERVICE_UNAVAILABLE, "AI_SERVER_UNAVAILABLE");

    private final HttpStatus status;
    private final String code;
}