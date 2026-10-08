package com.quantx.research.dto;

import com.quantx.research.ResearchRequest;
import com.quantx.research.ResearchRequestStatus;
import java.time.LocalDateTime;
import java.util.List;

public record ResearchRequestDto(
        Long id,
        String userId,
        String query,
        List<String> scope,
        String priority,
        ResearchRequestStatus status,
        String jobId,
        LocalDateTime createdAt,
        LocalDateTime startedAt,
        LocalDateTime finishedAt
) {
    public static ResearchRequestDto of(ResearchRequest r) {
        return new ResearchRequestDto(r.getId(), r.getUserId(), r.getQuery(),
                r.getScope(), r.getPriority(), r.getStatus(), r.getJobId(),
                r.getCreatedAt(), r.getStartedAt(), r.getFinishedAt());
    }
}