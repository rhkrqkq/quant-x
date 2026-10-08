package com.quantx.ai.dto;

import java.util.List;

public record RagSearchResponse(List<Hit> items, int total) {
	public record Hit(
		String chunkId, String docId, String title, String source,
		String publishedAt, String content, Double score, String trustLevel
	) {}
}