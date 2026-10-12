package com.quantx.order;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface OrderApprovalQueueRepository extends JpaRepository<OrderApprovalQueue, Long> {

	Optional<OrderApprovalQueue> findByOrderId(String orderId);

	List<OrderApprovalQueue> findByStatusOrderByCreatedAtAsc(String status);
}