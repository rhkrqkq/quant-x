package com.quantx.research.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.List;

public record CreateResearchRequest(
        @NotBlank @Size(max = 4000) String query,
        List<String> scope,
        String priority
) {}