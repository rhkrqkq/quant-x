package com.quantx.research;

import com.quantx.ai.AiClient;
import com.quantx.ai.dto.AiJobStatus;
import com.quantx.ai.dto.AiResearchRequest;
import com.quantx.common.ApiException;
import com.quantx.common.ErrorCode;
import com.quantx.research.dto.CreateResearchRequest;
import com.quantx.research.dto.ExecuteResponse;
import com.quantx.research.dto.ResearchRequestDto;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class ResearchService {

    private final ResearchRequestRepository repository;
    private final AiClient aiClient;

    @Transactional
    public ResearchRequestDto create(String userId, CreateResearchRequest req) {
        ResearchRequest entity = ResearchRequest.builder()
                .userId(userId)
                .query(req.query())
                .scope(req.scope() != null ? req.scope() : List.of())
                .priority(req.priority() != null ? req.priority() : "NORMAL")
                .status(ResearchRequestStatus.CREATED)
                .build();
        return ResearchRequestDto.of(repository.save(entity));
    }

    @Transactional(readOnly = true)
    public Page<ResearchRequestDto> list(String userId, Pageable pageable) {
        return repository.findByUserIdOrderByIdDesc(userId, pageable)
                .map(ResearchRequestDto::of);
    }

    @Transactional(readOnly = true)
    public ResearchRequestDto get(Long id, String userId) {
        ResearchRequest r = repository.findById(id)
                .orElseThrow(() -> new ApiException(ErrorCode.NOT_FOUND, "요청을 찾을 수 없음"));
        if (!r.getUserId().equals(userId)) {
            throw new ApiException(ErrorCode.FORBIDDEN, "타인의 요청에 접근 불가");
        }
        return ResearchRequestDto.of(r);
    }

    @Transactional
    public ExecuteResponse execute(Long id, String userId) {
        ResearchRequest r = repository.findById(id)
                .orElseThrow(() -> new ApiException(ErrorCode.NOT_FOUND, "요청을 찾을 수 없음"));
        if (!r.getUserId().equals(userId)) {
            throw new ApiException(ErrorCode.FORBIDDEN, "타인의 요청에 접근 불가");
        }
        if (r.getStatus() != ResearchRequestStatus.CREATED) {
            throw new ApiException(ErrorCode.VALIDATION_ERROR,
                    "이미 실행되었거나 완료된 요청: " + r.getStatus());
        }

        AiResearchRequest aiReq = new AiResearchRequest(
                r.getId(), userId, r.getQuery(), r.getScope(), null);
        AiJobStatus job = aiClient.startResearch(aiReq);

        r.markRunning(job.jobId());
        return new ExecuteResponse(r.getId(), job.jobId(), r.getStatus());
    }

    @Transactional
    public ResearchRequestDto refreshStatus(Long id, String userId) {
        ResearchRequest r = repository.findById(id)
                .orElseThrow(() -> new ApiException(ErrorCode.NOT_FOUND, "요청 없음"));
        if (!r.getUserId().equals(userId)) {
            throw new ApiException(ErrorCode.FORBIDDEN, "권한 없음");
        }
        if (r.getStatus() == ResearchRequestStatus.RUNNING && r.getJobId() != null) {
            AiJobStatus job = aiClient.getJob(r.getJobId());
            switch (job.status()) {
                case "COMPLETED" -> r.markCompleted();
                case "FAILED" -> r.markFailed();
                // RUNNING은 그대로
            }
        }
        return ResearchRequestDto.of(r);
    }
}