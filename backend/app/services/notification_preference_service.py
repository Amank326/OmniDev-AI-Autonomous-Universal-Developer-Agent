"""
Notification Preference Service - User notification settings management
Phase 27: Advanced Notifications & Real-time Alerts System
"""

import uuid
from datetime import datetime, time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class NotificationChannel(Enum):
    """Notification channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class AlertSeverity(Enum):
    """Alert severity levels for filtering"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    URGENT = "urgent"


@dataclass
class DoNotDisturbSchedule:
    """Do Not Disturb time period"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: time = field(default_factory=lambda: time(22, 0))  # 10 PM
    end_time: time = field(default_factory=lambda: time(8, 0))    # 8 AM
    enabled: bool = True
    allow_urgent: bool = True  # Allow urgent alerts during DND


@dataclass
class ChannelPreference:
    """Preference settings for a specific channel"""
    channel: NotificationChannel = NotificationChannel.IN_APP
    enabled: bool = True
    priority: int = 1  # 1 = highest, 5 = lowest
    min_severity: AlertSeverity = AlertSeverity.INFO
    frequency_cap: Optional[int] = None  # Max notifications per hour
    batch_hours: int = 0  # 0 = instant, >0 = batch delivery


@dataclass
class NotificationPreference:
    """Complete user notification preferences"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    channel_preferences: Dict[str, ChannelPreference] = field(default_factory=dict)
    dnd_schedules: List[DoNotDisturbSchedule] = field(default_factory=list)
    globally_enabled: bool = True
    alert_types_enabled: Dict[str, bool] = field(default_factory=dict)
    keywords_to_follow: List[str] = field(default_factory=list)
    muted_keywords: List[str] = field(default_factory=list)
    auto_archive_threshold_days: int = 30
    max_daily_notifications: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class NotificationFrequencyStats:
    """Track notification frequency for rate limiting"""
    channel: NotificationChannel = NotificationChannel.IN_APP
    count: int = 0
    hour_start: datetime = field(default_factory=datetime.utcnow)


class NotificationPreferenceService:
    """Service for managing user notification preferences"""

    def __init__(self):
        self.preferences: Dict[str, NotificationPreference] = {}
        self.frequency_stats: Dict[str, List[NotificationFrequencyStats]] = {}
        self._init_default_preferences()

    def _init_default_preferences(self):
        """Initialize default preference templates"""
        self.default_channels = {
            NotificationChannel.EMAIL.value: ChannelPreference(
                channel=NotificationChannel.EMAIL,
                enabled=True,
                priority=2,
                min_severity=AlertSeverity.WARNING,
                frequency_cap=10,
                batch_hours=1
            ),
            NotificationChannel.SMS.value: ChannelPreference(
                channel=NotificationChannel.SMS,
                enabled=False,
                priority=1,
                min_severity=AlertSeverity.CRITICAL,
                frequency_cap=3
            ),
            NotificationChannel.PUSH.value: ChannelPreference(
                channel=NotificationChannel.PUSH,
                enabled=True,
                priority=3,
                min_severity=AlertSeverity.WARNING,
                frequency_cap=20
            ),
            NotificationChannel.IN_APP.value: ChannelPreference(
                channel=NotificationChannel.IN_APP,
                enabled=True,
                priority=4,
                min_severity=AlertSeverity.INFO,
                frequency_cap=None  # No cap for in-app
            ),
        }

    def get_or_create_preferences(self, user_id: str) -> NotificationPreference:
        """Get user preferences or create defaults"""
        if user_id in self.preferences:
            return self.preferences[user_id]

        preferences = NotificationPreference(
            user_id=user_id,
            channel_preferences=self.default_channels.copy(),
            dnd_schedules=[DoNotDisturbSchedule()]
        )
        self.preferences[user_id] = preferences
        return preferences

    def update_channel_preference(
        self,
        user_id: str,
        channel: NotificationChannel,
        enabled: bool,
        priority: int,
        min_severity: AlertSeverity,
        frequency_cap: Optional[int] = None
    ) -> bool:
        """Update preference for specific channel"""
        prefs = self.get_or_create_preferences(user_id)

        prefs.channel_preferences[channel.value] = ChannelPreference(
            channel=channel,
            enabled=enabled,
            priority=priority,
            min_severity=min_severity,
            frequency_cap=frequency_cap
        )

        prefs.updated_at = datetime.utcnow()
        return True

    def set_dnd_schedule(
        self,
        user_id: str,
        start_time: time,
        end_time: time,
        allow_urgent: bool = True
    ) -> DoNotDisturbSchedule:
        """Set Do Not Disturb schedule"""
        prefs = self.get_or_create_preferences(user_id)

        dnd = DoNotDisturbSchedule(
            start_time=start_time,
            end_time=end_time,
            allow_urgent=allow_urgent
        )

        # Replace existing DND, keep only one
        prefs.dnd_schedules = [dnd]
        prefs.updated_at = datetime.utcnow()

        return dnd

    def enable_dnd(self, user_id: str, enabled: bool) -> bool:
        """Enable/disable Do Not Disturb"""
        prefs = self.get_or_create_preferences(user_id)

        if prefs.dnd_schedules:
            prefs.dnd_schedules[0].enabled = enabled
            prefs.updated_at = datetime.utcnow()
            return True

        return False

    def set_frequency_cap(
        self,
        user_id: str,
        channel: NotificationChannel,
        cap: int
    ) -> bool:
        """Set max notifications per hour for channel"""
        prefs = self.get_or_create_preferences(user_id)

        if channel.value in prefs.channel_preferences:
            prefs.channel_preferences[channel.value].frequency_cap = cap
            prefs.updated_at = datetime.utcnow()
            return True

        return False

    def set_max_daily_notifications(self, user_id: str, max_count: int) -> bool:
        """Set global daily notification cap"""
        prefs = self.get_or_create_preferences(user_id)
        prefs.max_daily_notifications = max_count
        prefs.updated_at = datetime.utcnow()
        return True

    def enable_globally(self, user_id: str, enabled: bool) -> bool:
        """Enable/disable all notifications"""
        prefs = self.get_or_create_preferences(user_id)
        prefs.globally_enabled = enabled
        prefs.updated_at = datetime.utcnow()
        return True

    def add_keyword_to_follow(self, user_id: str, keyword: str) -> bool:
        """Add keyword for notification follow"""
        prefs = self.get_or_create_preferences(user_id)

        if keyword not in prefs.keywords_to_follow:
            prefs.keywords_to_follow.append(keyword)
            prefs.updated_at = datetime.utcnow()

        return True

    def remove_keyword_to_follow(self, user_id: str, keyword: str) -> bool:
        """Remove keyword from follow list"""
        prefs = self.get_or_create_preferences(user_id)

        if keyword in prefs.keywords_to_follow:
            prefs.keywords_to_follow.remove(keyword)
            prefs.updated_at = datetime.utcnow()
            return True

        return False

    def add_muted_keyword(self, user_id: str, keyword: str) -> bool:
        """Mute notifications containing keyword"""
        prefs = self.get_or_create_preferences(user_id)

        if keyword not in prefs.muted_keywords:
            prefs.muted_keywords.append(keyword)
            prefs.updated_at = datetime.utcnow()

        return True

    def remove_muted_keyword(self, user_id: str, keyword: str) -> bool:
        """Unmute keyword"""
        prefs = self.get_or_create_preferences(user_id)

        if keyword in prefs.muted_keywords:
            prefs.muted_keywords.remove(keyword)
            prefs.updated_at = datetime.utcnow()
            return True

        return False

    def should_suppress_notification(
        self,
        user_id: str,
        channel: NotificationChannel,
        severity: AlertSeverity
    ) -> bool:
        """Check if notification should be suppressed based on preferences"""
        if not self.is_notifications_enabled(user_id):
            return True

        prefs = self.get_or_create_preferences(user_id)

        # Check channel enabled
        if channel.value not in prefs.channel_preferences:
            return True

        channel_pref = prefs.channel_preferences[channel.value]
        if not channel_pref.enabled:
            return True

        # Check severity threshold
        severity_order = [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.CRITICAL, AlertSeverity.URGENT]
        if severity_order.index(severity) < severity_order.index(channel_pref.min_severity):
            return True

        # Check DND schedule
        if self._is_in_dnd(user_id):
            # Allow urgent during DND if configured
            if severity != AlertSeverity.URGENT:
                return True
            if not prefs.dnd_schedules or not prefs.dnd_schedules[0].allow_urgent:
                return True

        return False

    def _is_in_dnd(self, user_id: str) -> bool:
        """Check if currently in Do Not Disturb"""
        prefs = self.get_or_create_preferences(user_id)

        if not prefs.dnd_schedules or not prefs.dnd_schedules[0].enabled:
            return False

        now = datetime.utcnow().time()
        dnd = prefs.dnd_schedules[0]

        # Handle overnight DND (e.g., 22:00 to 08:00)
        if dnd.start_time < dnd.end_time:
            return dnd.start_time <= now <= dnd.end_time
        else:
            return now >= dnd.start_time or now <= dnd.end_time

    def is_notifications_enabled(self, user_id: str) -> bool:
        """Check if notifications are globally enabled"""
        prefs = self.get_or_create_preferences(user_id)
        return prefs.globally_enabled

    def get_enabled_channels(self, user_id: str) -> List[NotificationChannel]:
        """Get list of enabled notification channels"""
        prefs = self.get_or_create_preferences(user_id)
        enabled = []

        for channel_name, pref in prefs.channel_preferences.items():
            if pref.enabled:
                enabled.append(pref.channel)

        # Sort by priority
        enabled.sort(key=lambda c: prefs.channel_preferences[c.value].priority)
        return enabled

    def check_frequency_cap(
        self,
        user_id: str,
        channel: NotificationChannel
    ) -> bool:
        """Check if frequency cap would be exceeded"""
        prefs = self.get_or_create_preferences(user_id)

        if channel.value not in prefs.channel_preferences:
            return False

        channel_pref = prefs.channel_preferences[channel.value]
        if not channel_pref.frequency_cap:
            return True  # No cap

        # Get stats for this hour
        stats = self.frequency_stats.get(f"{user_id}_{channel.value}", [])
        current_count = sum([s.count for s in stats])

        return current_count < channel_pref.frequency_cap

    def record_notification_sent(self, user_id: str, channel: NotificationChannel) -> None:
        """Record that notification was sent for frequency tracking"""
        key = f"{user_id}_{channel.value}"

        if key not in self.frequency_stats:
            self.frequency_stats[key] = []

        # Find or create current hour stat
        now = datetime.utcnow()
        current_hour = now.replace(minute=0, second=0, microsecond=0)

        stat = next(
            (s for s in self.frequency_stats[key] if s.hour_start == current_hour),
            None
        )

        if stat:
            stat.count += 1
        else:
            stat = NotificationFrequencyStats(channel=channel, count=1, hour_start=current_hour)
            self.frequency_stats[key].append(stat)

    def get_preferences(self, user_id: str) -> Optional[NotificationPreference]:
        """Get user preferences"""
        return self.preferences.get(user_id)

    def export_preferences(self, user_id: str) -> Dict[str, Any]:
        """Export preferences as dict"""
        prefs = self.get_or_create_preferences(user_id)

        return {
            "globally_enabled": prefs.globally_enabled,
            "channels": {
                ch_name: {
                    "enabled": ch.enabled,
                    "priority": ch.priority,
                    "min_severity": ch.min_severity.value,
                    "frequency_cap": ch.frequency_cap
                }
                for ch_name, ch in prefs.channel_preferences.items()
            },
            "dnd": {
                "start_time": prefs.dnd_schedules[0].start_time.isoformat() if prefs.dnd_schedules else None,
                "end_time": prefs.dnd_schedules[0].end_time.isoformat() if prefs.dnd_schedules else None,
                "enabled": prefs.dnd_schedules[0].enabled if prefs.dnd_schedules else False,
                "allow_urgent": prefs.dnd_schedules[0].allow_urgent if prefs.dnd_schedules else True
            },
            "keywords_to_follow": prefs.keywords_to_follow,
            "muted_keywords": prefs.muted_keywords,
            "max_daily_notifications": prefs.max_daily_notifications,
            "auto_archive_days": prefs.auto_archive_threshold_days
        }
