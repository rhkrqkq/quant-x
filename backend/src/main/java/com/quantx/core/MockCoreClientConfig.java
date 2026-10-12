package com.quantx.core;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;

/**
 * Core Zone 호출용 WebClient. AiClientConfig와 같은 모양이지만 키가 다르다.
 * <p>
 * [보안] 시스템 키는 이 서버에만 있다. AI 서버에는 Read 키만 준다.
 * 두 키를 한 프로세스에 두면 분리한 의미가 없다.
 */
@Configuration
public class MockCoreClientConfig {

	@Bean
	public WebClient mockCoreWebClient(
		@Value("${quantx.mock-core.base-url}") String baseUrl,
		@Value("${quantx.mock-core.system-key}") String systemKey,
		@Value("${quantx.mock-core.timeout-seconds}") long timeoutSeconds) {

		HttpClient http = HttpClient.create()
			.responseTimeout(Duration.ofSeconds(timeoutSeconds));

		return WebClient.builder()
			.baseUrl(baseUrl)
			.clientConnector(new ReactorClientHttpConnector(http))
			.defaultHeader(HttpHeaders.CONTENT_TYPE, "application/json")
			.defaultHeader("X-System-Key", systemKey)
			.defaultHeader("X-Caller", "spring-boot")   // Mock Core 감사 로그에 남는다
			.build();
	}
}