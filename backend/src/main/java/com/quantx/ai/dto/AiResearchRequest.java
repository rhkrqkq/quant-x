package com.quantx.ai.dto;

import java.util.List;
import java.util.Map;

public record AiResearchRequest(
        Long requestId,
        String userId,
        String query,
        List<String> scope,
        Map<String, Object> options
) {}