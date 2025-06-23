"""Constants for LMNOP."""

from logging import Logger, getLogger
from typing import Final

LOGGER: Logger = getLogger(__package__)

DOMAIN: Final = "lmnop"
DEFAULT_NAME: Final = "LMNOP Notifier"

# Configuration constants
CONF_ALERT_LIGHT_GROUP: Final = "alert_light_group"

# Notification data keys
ATTR_PRIORITY: Final = "priority"

# Priority levels
PRIORITY_CRITICAL: Final = "critical"  # Security alerts, system failures, emergencies
PRIORITY_HIGH: Final = "high"  # Important but not emergency situations
PRIORITY_MEDIUM: Final = "medium"  # Regular household notifications
PRIORITY_LOW: Final = "low"  # Informational updates
PRIORITY_DEBUG: Final = "debug"  # System/technical information

# Alert priorities that trigger lights
ALERT_PRIORITIES: Final = [PRIORITY_CRITICAL, PRIORITY_HIGH]

# Light alert constants
ALERT_RGB_COLOR: Final = [255, 0, 0]  # Full brightness red
ALERT_BRIGHTNESS: Final = 255
