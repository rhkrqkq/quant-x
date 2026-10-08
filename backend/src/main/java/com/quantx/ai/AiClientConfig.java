package com.quantx.ai;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;

@Configuration
public class AiClientConfig {

    @Bean
    public WebClient aiWebClient(
            @Value("${quantx.ai-server.base-url}") String baseUrl,
            @Value("${quantx.ai-server.api-key}") String apiKey,
            @Value("${quantx.ai-server.timeout-seconds}") long timeoutSeconds) {

        HttpClient http = HttpClient.create()
                .responseTimeout(Duration.ofSeconds(timeoutSeconds));

        return WebClient.builder()
                .baseUrl(baseUrl)
                .clientConnector(new ReactorClientHttpConnector(http))
                .defaultHeader(HttpHeaders.CONTENT_TYPE, "application/json")
                .defaultHeader("X-Internal-API-Key", apiKey)
                .build();
    }
}