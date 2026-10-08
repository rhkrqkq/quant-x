package com.quantx.ai.dto;

import java.util.List;

public record RagSearchRequest(
	String query,
	List<String> scope,
	int topK,
	Double minScore,
	List<String> trustLevels,
	String dateFrom
) {
	public static RagSearchRequest of(String query) {
		return new RagSearchRequest(query, List.of("RAG_READ"), 5, 0.4,
			List.of("HIGH", "MEDIUM"), null);
	}
}