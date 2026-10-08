package com.quantx.research;

import com.quantx.common.BaseEntity;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "research_request")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class ResearchRequest extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false, length = 64)
    private String userId;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String query;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "scope_json", columnDefinition = "LONGTEXT")
    private List<String> scope;

    @Column(nullable = false, length = 16)
    private String priority;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private ResearchRequestStatus status;

    @Column(name = "job_id", length = 64)
    private String jobId;

    @Column(name = "started_at")
    private LocalDateTime startedAt;

    @Column(name = "finished_at")
    private LocalDateTime finishedAt;

    public void markRunning(String jobId) {
        this.status = ResearchRequestStatus.RUNNING;
        this.jobId = jobId;
        this.startedAt = LocalDateTime.now();
    }

    public void markCompleted() {
        this.status = ResearchRequestStatus.COMPLETED;
        this.finishedAt = LocalDateTime.now();
    }

    public void markFailed() {
        this.status = ResearchRequestStatus.FAILED;
        this.finishedAt = LocalDateTime.now();
    }
}