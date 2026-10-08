package com.quantx.research;

import com.quantx.common.ApiResponse;
import com.quantx.research.dto.CreateResearchRequest;
import com.quantx.research.dto.ExecuteResponse;
import com.quantx.research.dto.ResearchRequestDto;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/research-requests")
@RequiredArgsConstructor
public class ResearchRequestController {

    private final ResearchService service;

    @PostMapping
    @PreAuthorize("hasAuthority('SCOPE_RAG_READ') or hasAuthority('SCOPE_MARKET_DATA_READ')")
    public ApiResponse<ResearchRequestDto> create(
            @AuthenticationPrincipal String userId,
            @Valid @RequestBody CreateResearchRequest req) {
        return ApiResponse.success(service.create(userId, req));
    }

    @GetMapping
    public ApiResponse<Page<ResearchRequestDto>> list(
            @AuthenticationPrincipal String userId,
            Pageable pageable) {
        return ApiResponse.success(service.list(userId, pageable));
    }

    @GetMapping("/{id}")
    public ApiResponse<ResearchRequestDto> get(
            @AuthenticationPrincipal String userId,
            @PathVariable Long id) {
        return ApiResponse.success(service.get(id, userId));
    }

    @PostMapping("/{id}/execute")
    public ApiResponse<ExecuteResponse> execute(
            @AuthenticationPrincipal String userId,
            @PathVariable Long id) {
        return ApiResponse.success(service.execute(id, userId));
    }

    @GetMapping("/{id}/status")
    public ApiResponse<ResearchRequestDto> status(
            @AuthenticationPrincipal String userId,
            @PathVariable Long id) {
        return ApiResponse.success(service.refreshStatus(id, userId));
    }
}