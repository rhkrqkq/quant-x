package com.quantx.research;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ResearchRequestRepository extends JpaRepository<ResearchRequest, Long> {
    Page<ResearchRequest> findByUserIdOrderByIdDesc(String userId, Pageable pageable);
}