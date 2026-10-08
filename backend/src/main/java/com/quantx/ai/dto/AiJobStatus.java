package com.quantx.ai.dto;

import java.util.Map;

public record AiJobStatus(
        String jobId,
        String status,        // RUNNING, COMPLETED, FAILED
        Double progress,
        String currentStep,
        Map<String, Object> result
) {}