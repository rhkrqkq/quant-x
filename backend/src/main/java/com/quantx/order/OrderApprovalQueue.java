package com.quantx.order;

import com.quantx.common.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

/**
 * 결재 큐. Core Zone의 주문을 그대로 복제하는 것이 아니라, 결재라는 사내 절차를 남기는 곳이다.
 * <p>
 * 체결 사실은 Core Zone이 원본을 갖고, 누가 언제 무슨 의견으로 승인했는지는 여기가 갖는다.
 */
@Entity
@Table(name = "order_approval_queue")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class OrderApprovalQueue extends BaseEntity {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(name = "order_id", nullable = false, unique = true, length = 64)
	private String orderId;

	@Column(name = "research_report_id")
	private Long researchReportId;

	@Column(name = "account_id", nullable = false, length = 32)
	private String accountId;

	@Column(nullable = false, length = 16)
	private String ticker;

	@Column(nullable = false, length = 8)
	private String side;

	@Column(nullable = false)
	private Integer quantity;

	@Column(nullable = false)
	private Integer price;

	@Column(name = "estimated_amount_krw", nullable = false)
	private Long estimatedAmountKrw;

	@Column(name = "submitted_by", nullable = false, length = 64)
	private String submittedBy;

	@Column(nullable = false, length = 16)
	private String status;

	@Column(name = "decided_by", length = 64)
	private String decidedBy;

	@Column(name = "decided_at")
	private LocalDateTime decidedAt;

	@Column(columnDefinition = "TEXT")
	private String comment;

	/** Core Zone의 결정을 사내 기록에 반영한다. */
	public void applyDecision(String status, String decidedBy, String comment) {
		this.status = status;
		this.decidedBy = decidedBy;
		this.decidedAt = LocalDateTime.now();
		this.comment = comment;
	}
}