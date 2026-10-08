package com.quantx.ai;

import com.quantx.ai.dto.AiJobStatus;
import com.quantx.ai.dto.AiResearchRequest;
import com.quantx.ai.dto.RagSearchRequest;
import com.quantx.ai.dto.RagSearchResponse;
import com.quantx.common.ApiException;
import com.quantx.common.ErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

@Component
@RequiredArgsConstructor
@Slf4j
public class AiClient {

    private final WebClient aiWebClient;

    public AiJobStatus startResearch(AiResearchRequest req) {
        try {
            return aiWebClient.post()
                    .uri("/ai/research")
                    .header("X-User-Id", req.userId())
                    .bodyValue(req)
                    .retrieve()
                    .bodyToMono(AiJobStatus.class)
                    .block();
        } catch (WebClientResponseException.ServiceUnavailable e) {
            log.warn("AI server unavailable: {}", e.getStatusCode());
            throw new ApiException(ErrorCode.AI_SERVER_UNAVAILABLE, "AI 서버 응답 없음");
        } catch (WebClientResponseException e) {
            log.error("AI server error: {} {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new ApiException(ErrorCode.LLM_PROVIDER_ERROR, "AI 처리 오류", e.getResponseBodyAsString());
        }
    }

    public AiJobStatus getJob(String jobId) {
        try {
            return aiWebClient.get()
                    .uri("/ai/jobs/{jobId}", jobId)
                    .retrieve()
                    .bodyToMono(AiJobStatus.class)
                    .block();
        } catch (WebClientResponseException.NotFound e) {
            throw new ApiException(ErrorCode.NOT_FOUND, "Job 없음");
        } catch (WebClientResponseException e) {
            throw new ApiException(ErrorCode.LLM_PROVIDER_ERROR, "AI Job 조회 오류");
        }
    }

    public RagSearchResponse ragSearch(RagSearchRequest req, String userId) {
        return aiWebClient.post()
            .uri("/ai/rag/search")
            .header("X-User-Id", userId)            // FastAPI 측 require_user_id 의존성과 짝
            .bodyValue(req)
            .retrieve()
            .bodyToMono(RagSearchResponse.class)
            .block();
    }
}