"""
Dunning Service - Handle failed payment recovery and retry logic
Manages payment failures, retry schedules, notifications, and recovery strategies
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json

class DunningStrategy(str, Enum):
    """Dunning/payment recovery strategies"""
    AGGRESSIVE = "aggressive"  # Frequent retries, immediate notifications
    MODERATE = "moderate"      # Balanced retry schedule
    CONSERVATIVE = "conservative"  # Infrequent retries, gentle approach
    CUSTOM = "custom"          # Custom configuration


class RetryStatus(str, Enum):
    """Retry attempt status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"


class NotificationType(str, Enum):
    """Dunning notification types"""
    PAYMENT_FAILED = "payment_failed"
    RETRY_SCHEDULED = "retry_scheduled"
    MULTIPLE_FAILURES = "multiple_failures"
    PAYMENT_RECOVERED = "payment_recovered"
    SUBSCRIPTION_AT_RISK = "subscription_at_risk"
    FINAL_NOTICE = "final_notice"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"


class DunningService:
    """
    Service for payment failure recovery and dunning management.
    Handles retry schedules, notifications, and recovery strategies.
    """
    
    def __init__(self):
        """Initialize dunning service with retry strategies"""
        self.failed_payments = {}
        self.retry_schedules = {}
        self.notifications = {}
        self.recovery_metrics = {}
        self.notification_counter = 0
        
        # Retry configurations by strategy
        self.retry_configs = {
            DunningStrategy.AGGRESSIVE: {
                "max_attempts": 8,
                "retry_intervals": [1, 3, 5, 7, 14, 21, 30, 45],  # Days between retries
                "notification_frequency": "every_retry",
                "escalation_levels": 4,
            },
            DunningStrategy.MODERATE: {
                "max_attempts": 5,
                "retry_intervals": [3, 7, 14, 21, 30],
                "notification_frequency": "every_other_retry",
                "escalation_levels": 3,
            },
            DunningStrategy.CONSERVATIVE: {
                "max_attempts": 3,
                "retry_intervals": [7, 14, 30],
                "notification_frequency": "on_failure",
                "escalation_levels": 2,
            },
            DunningStrategy.CUSTOM: {
                "max_attempts": 5,
                "retry_intervals": [3, 7, 14, 21, 30],
                "notification_frequency": "every_retry",
                "escalation_levels": 3,
            },
        }
        
        # Escalation messages
        self.escalation_messages = {
            1: "Payment failed. We'll retry in a few days.",
            2: "We couldn't process your payment. Please update your billing info.",
            3: "Your subscription is at risk due to payment failures.",
            4: "Final notice: Please resolve payment or your account will be cancelled.",
        }
    
    def process_failed_payment(
        self,
        subscription_id: str,
        customer_id: str,
        amount: float,
        currency: str,
        payment_method: str,
        error_code: str,
        error_message: str,
        customer_email: str,
        dunning_strategy: DunningStrategy = DunningStrategy.MODERATE,
    ) -> Dict:
        """
        Process a failed payment and initiate recovery.
        Records failure, generates retry schedule, and sends notification.
        
        Args:
            subscription_id: Subscription that failed
            customer_id: Customer ID
            amount: Failed payment amount
            currency: Currency code
            payment_method: Payment method that failed
            error_code: Error code from payment processor
            error_message: Human-readable error
            customer_email: Customer email for notifications
            dunning_strategy: Recovery strategy to apply
        
        Returns:
            Failed payment record with retry schedule
        """
        failure_id = f"fail_{len(self.failed_payments) + 1}"
        
        failed_payment = {
            "failure_id": failure_id,
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "error_code": error_code,
            "error_message": error_message,
            "customer_email": customer_email,
            "dunning_strategy": dunning_strategy.value,
            "first_failure_date": datetime.utcnow().isoformat(),
            "last_failure_date": datetime.utcnow().isoformat(),
            "failure_count": 1,
            "status": RetryStatus.PENDING.value,
        }
        
        self.failed_payments[failure_id] = failed_payment
        
        # Generate retry schedule
        retry_schedule = self.generate_retry_schedule(
            failure_id,
            subscription_id,
            dunning_strategy,
        )
        
        # Send initial notification
        notification = self.send_notification(
            failure_id,
            customer_id,
            customer_email,
            NotificationType.PAYMENT_FAILED,
            {
                "amount": amount,
                "currency": currency,
                "error": error_message,
                "next_retry": retry_schedule["retry_dates"][0] if retry_schedule["retry_dates"] else None,
            }
        )
        
        return {
            "failure_id": failure_id,
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "status": RetryStatus.PENDING.value,
            "dunning_strategy": dunning_strategy.value,
            "retry_schedule": retry_schedule,
            "notification_sent": notification,
            "first_failure": failed_payment["first_failure_date"],
        }
    
    def generate_retry_schedule(
        self,
        failure_id: str,
        subscription_id: str,
        dunning_strategy: DunningStrategy,
        custom_config: Optional[Dict] = None,
    ) -> Dict:
        """
        Generate retry schedule for failed payment.
        Creates scheduled retry attempts based on strategy.
        
        Args:
            failure_id: Failed payment ID
            subscription_id: Subscription ID
            dunning_strategy: Strategy to apply
            custom_config: Optional custom configuration
        
        Returns:
            Retry schedule with dates and attempt details
        """
        if failure_id not in self.failed_payments:
            raise ValueError(f"Failed payment {failure_id} not found")
        
        # Get strategy config
        config = custom_config or self.retry_configs.get(
            dunning_strategy,
            self.retry_configs[DunningStrategy.MODERATE]
        )
        
        retry_intervals = config.get("retry_intervals", [3, 7, 14, 21, 30])
        max_attempts = config.get("max_attempts", 5)
        
        # Generate retry dates
        base_date = datetime.utcnow()
        retry_dates = []
        retry_attempts = []
        
        for attempt_num, days_offset in enumerate(retry_intervals[:max_attempts], 1):
            retry_date = base_date + timedelta(days=days_offset)
            retry_dates.append(retry_date.isoformat())
            
            # Determine escalation level
            escalation_level = min(
                (attempt_num - 1) // 2 + 1,  # Escalate every 2 attempts
                config.get("escalation_levels", 3)
            )
            
            retry_attempts.append({
                "attempt_number": attempt_num,
                "scheduled_date": retry_date.isoformat(),
                "days_after_failure": days_offset,
                "escalation_level": escalation_level,
                "status": RetryStatus.PENDING.value,
                "escalation_message": self.escalation_messages.get(
                    escalation_level,
                    "Payment recovery attempt"
                ),
            })
        
        schedule = {
            "failure_id": failure_id,
            "subscription_id": subscription_id,
            "strategy": dunning_strategy.value,
            "max_attempts": max_attempts,
            "retry_dates": retry_dates,
            "retry_attempts": retry_attempts,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.retry_schedules[failure_id] = schedule
        return schedule
    
    def send_notifications(
        self,
        failure_ids: List[str],
    ) -> List[Dict]:
        """
        Send notifications for multiple failed payments.
        Batch notification processing.
        
        Args:
            failure_ids: List of failure IDs
        
        Returns:
            List of sent notifications
        """
        notifications = []
        for failure_id in failure_ids:
            if failure_id in self.failed_payments:
                payment = self.failed_payments[failure_id]
                notification = self.send_notification(
                    failure_id,
                    payment["customer_id"],
                    payment["customer_email"],
                    NotificationType.RETRY_SCHEDULED,
                )
                notifications.append(notification)
        
        return notifications
    
    def send_notification(
        self,
        failure_id: str,
        customer_id: str,
        customer_email: str,
        notification_type: NotificationType,
        context: Optional[Dict] = None,
    ) -> Dict:
        """
        Send notification for payment failure.
        Supports email, SMS, and in-app notifications.
        
        Args:
            failure_id: Failed payment ID
            customer_id: Customer ID
            customer_email: Customer email
            notification_type: Type of notification
            context: Additional context for message
        
        Returns:
            Notification record
        """
        self.notification_counter += 1
        notification_id = f"notif_{self.notification_counter}"
        
        # Generate message based on type
        message = self._generate_notification_message(
            notification_type,
            context or {}
        )
        
        notification = {
            "notification_id": notification_id,
            "failure_id": failure_id,
            "customer_id": customer_id,
            "email": customer_email,
            "type": notification_type.value,
            "subject": self._get_notification_subject(notification_type),
            "message": message,
            "channels": ["email", "in-app"],  # Send via multiple channels
            "sent_at": datetime.utcnow().isoformat(),
            "status": "sent",
        }
        
        self.notifications[notification_id] = notification
        return notification
    
    def _generate_notification_message(
        self,
        notification_type: NotificationType,
        context: Dict,
    ) -> str:
        """Generate notification message based on type"""
        messages = {
            NotificationType.PAYMENT_FAILED: (
                f"We couldn't process your payment of {context.get('currency', 'USD')} "
                f"{context.get('amount', '0')}. Error: {context.get('error', 'Unknown error')}. "
                f"We'll retry on {context.get('next_retry', 'soon')}."
            ),
            NotificationType.RETRY_SCHEDULED: (
                "Your payment is scheduled to retry soon. "
                "Please ensure your billing information is up to date."
            ),
            NotificationType.MULTIPLE_FAILURES: (
                "We've had trouble processing your payments. "
                "Please update your billing information immediately."
            ),
            NotificationType.PAYMENT_RECOVERED: (
                "Great news! Your payment was processed successfully. "
                "Your subscription is active."
            ),
            NotificationType.SUBSCRIPTION_AT_RISK: (
                "Your subscription is at risk due to payment failures. "
                "Please update your payment method to avoid cancellation."
            ),
            NotificationType.FINAL_NOTICE: (
                "Final notice: Your subscription will be cancelled if payment is not received. "
                "Update your billing information now."
            ),
            NotificationType.SUBSCRIPTION_CANCELLED: (
                "Your subscription has been cancelled due to unpaid invoices. "
                "Contact support to reactivate."
            ),
        }
        
        return messages.get(
            notification_type,
            "Your account requires attention regarding payment."
        )
    
    def _get_notification_subject(self, notification_type: NotificationType) -> str:
        """Get email subject for notification type"""
        subjects = {
            NotificationType.PAYMENT_FAILED: "Payment Failed - We'll Retry",
            NotificationType.RETRY_SCHEDULED: "Payment Retry Scheduled",
            NotificationType.MULTIPLE_FAILURES: "Action Required: Update Payment Method",
            NotificationType.PAYMENT_RECOVERED: "Payment Successful",
            NotificationType.SUBSCRIPTION_AT_RISK: "Subscription at Risk",
            NotificationType.FINAL_NOTICE: "Final Notice: Subscription Cancellation Pending",
            NotificationType.SUBSCRIPTION_CANCELLED: "Subscription Cancelled",
        }
        
        return subjects.get(notification_type, "Payment Status Update")
    
    def track_dunning_metrics(
        self,
        organization_id: str,
        date_range_days: int = 30,
    ) -> Dict:
        """
        Track dunning/recovery metrics for organization.
        Shows recovery rate, notification effectiveness, strategy performance.
        
        Args:
            organization_id: Organization ID
            date_range_days: Days to analyze
        
        Returns:
            Dunning metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=date_range_days)
        
        total_failures = 0
        recovered = 0
        still_failing = 0
        max_retries_exceeded = 0
        
        strategy_performance = {}
        notification_sent_count = 0
        
        for payment in self.failed_payments.values():
            failure_date = datetime.fromisoformat(payment["first_failure_date"])
            if failure_date < cutoff_date:
                continue
            
            total_failures += 1
            strategy = payment["dunning_strategy"]
            
            if strategy not in strategy_performance:
                strategy_performance[strategy] = {
                    "attempts": 0,
                    "recovered": 0,
                    "recovery_rate": 0,
                }
            
            strategy_performance[strategy]["attempts"] += 1
            
            # Track status
            if payment["status"] == RetryStatus.SUCCESS.value:
                recovered += 1
                strategy_performance[strategy]["recovered"] += 1
            elif payment["status"] == RetryStatus.MAX_RETRIES_EXCEEDED.value:
                max_retries_exceeded += 1
            else:
                still_failing += 1
        
        # Calculate recovery rates
        for strategy in strategy_performance:
            attempts = strategy_performance[strategy]["attempts"]
            recovered_count = strategy_performance[strategy]["recovered"]
            strategy_performance[strategy]["recovery_rate"] = (
                (recovered_count / attempts * 100) if attempts > 0 else 0
            )
        
        # Count notifications
        for notif in self.notifications.values():
            notif_date = datetime.fromisoformat(notif["sent_at"])
            if notif_date >= cutoff_date:
                notification_sent_count += 1
        
        recovery_rate = (recovered / total_failures * 100) if total_failures > 0 else 0
        
        return {
            "organization_id": organization_id,
            "analysis_period_days": date_range_days,
            "total_failures": total_failures,
            "recovered_payments": recovered,
            "still_failing": still_failing,
            "max_retries_exceeded": max_retries_exceeded,
            "overall_recovery_rate": round(recovery_rate, 2),
            "notifications_sent": notification_sent_count,
            "strategy_performance": strategy_performance,
            "average_recovery_time_days": self._calculate_avg_recovery_time(),
        }
    
    def _calculate_avg_recovery_time(self) -> float:
        """Calculate average days to recovery for successful payments"""
        recovery_times = []
        
        for payment in self.failed_payments.values():
            if payment["status"] == RetryStatus.SUCCESS.value:
                first_failure = datetime.fromisoformat(payment["first_failure_date"])
                # Simulate recovery date (in practice, from transaction history)
                recovery_times.append(3)  # Simulated: 3 days average
        
        if recovery_times:
            return sum(recovery_times) / len(recovery_times)
        return 0
    
    def mark_payment_recovered(
        self,
        failure_id: str,
        transaction_id: str,
        recovery_method: str = "retry_attempt",
    ) -> Dict:
        """
        Mark failed payment as recovered.
        Updates status and sends recovery notification.
        
        Args:
            failure_id: Failed payment ID
            transaction_id: Successful transaction ID
            recovery_method: How payment was recovered
        
        Returns:
            Updated failed payment record
        """
        if failure_id not in self.failed_payments:
            raise ValueError(f"Failed payment {failure_id} not found")
        
        payment = self.failed_payments[failure_id]
        payment["status"] = RetryStatus.SUCCESS.value
        payment["recovered_at"] = datetime.utcnow().isoformat()
        payment["transaction_id"] = transaction_id
        payment["recovery_method"] = recovery_method
        
        # Send recovery notification
        self.send_notification(
            failure_id,
            payment["customer_id"],
            payment["customer_email"],
            NotificationType.PAYMENT_RECOVERED,
        )
        
        return payment
    
    def record_retry_attempt(
        self,
        failure_id: str,
        attempt_number: int,
        result: str,  # "success" or "failed"
        error_code: Optional[str] = None,
    ) -> Dict:
        """
        Record retry attempt result.
        Updates failure status and schedules next retry if needed.
        
        Args:
            failure_id: Failed payment ID
            attempt_number: Attempt number
            result: "success" or "failed"
            error_code: Optional error code if failed
        
        Returns:
            Updated retry record
        """
        if failure_id not in self.retry_schedules:
            raise ValueError(f"Retry schedule {failure_id} not found")
        
        schedule = self.retry_schedules[failure_id]
        
        # Update attempt status
        if attempt_number <= len(schedule["retry_attempts"]):
            attempt = schedule["retry_attempts"][attempt_number - 1]
            attempt["status"] = (
                RetryStatus.SUCCESS.value if result == "success"
                else RetryStatus.FAILED.value
            )
            attempt["result_at"] = datetime.utcnow().isoformat()
            if error_code:
                attempt["error_code"] = error_code
        
        # Update failed payment
        payment = self.failed_payments[failure_id]
        if result == "success":
            self.mark_payment_recovered(failure_id, f"txn_{failure_id}_{attempt_number}")
        else:
            payment["failure_count"] += 1
            payment["last_failure_date"] = datetime.utcnow().isoformat()
            
            # Check if max retries exceeded
            if attempt_number >= schedule["max_attempts"]:
                payment["status"] = RetryStatus.MAX_RETRIES_EXCEEDED.value
                self.send_notification(
                    failure_id,
                    payment["customer_id"],
                    payment["customer_email"],
                    NotificationType.FINAL_NOTICE,
                )
        
        return {
            "failure_id": failure_id,
            "attempt_number": attempt_number,
            "result": result,
            "updated_at": datetime.utcnow().isoformat(),
        }
