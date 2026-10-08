package com.quantx.research.dto;

import com.quantx.research.ResearchRequestStatus;

public record ExecuteResponse(Long requestId, String jobId, ResearchRequestStatus status) {}