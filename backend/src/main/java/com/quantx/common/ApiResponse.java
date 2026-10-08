package com.quantx.common;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.time.OffsetDateTime;
import java.util.UUID;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record ApiResponse<T>(
        boolean success,
        T data,
        ErrorPayload error,
        String requestId,
        OffsetDateTime timestamp
) {
    public record ErrorPayload(String code, String message, Object details) {}

    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(true, data, null, UUID.randomUUID().toString(),
                OffsetDateTime.now());
    }

    public static <T> ApiResponse<T> failure(String code, String message, Object details) {
        return new ApiResponse<>(false, null, new ErrorPayload(code, message, details),
                UUID.randomUUID().toString(), OffsetDateTime.now());
    }
}