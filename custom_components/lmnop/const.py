"""Constants for integration_blueprint."""

from logging import Logger, getLogger
from typing import Final

LOGGER: Logger = getLogger(__package__)

DOMAIN: Final = "lmnop"
DEFAULT_NAME: Final = "LMNOP Notifier"

# Notification data keys
ATTR_PRIORITY: Final = "priority"

# Priority levels
PRIORITY_CRITICAL: Final = "critical"  # Security alerts, system failures, emergencies
PRIORITY_HIGH: Final = "high"  # Important but not emergency situations
PRIORITY_MEDIUM: Final = "medium"  # Regular household notifications
PRIORITY_LOW: Final = "low"  # Informational updates
PRIORITY_DEBUG: Final = "debug"  # System/technical information
