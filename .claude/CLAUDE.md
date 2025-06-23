# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom notification integration based on the integration_blueprint template. It implements a notification service that can send messages to external services via API.

## Development Commands

```bash
# Initial setup - Install dependencies
./scripts/setup

# Start local Home Assistant instance with debug logging
./scripts/develop

# Format and lint code
./scripts/lint
```

## Architecture

### Integration Structure

The custom component follows Home Assistant's notify platform architecture:

- **__init__.py** - Integration setup using discovery.async_load_platform() for notify platform
- **config_flow.py** - UI-based configuration flow with API key authentication
- **notify.py** - BaseNotificationService implementation for sending notifications
- **api.py** - API client using aiohttp for external notification service communication
- **const.py** - Constants including notification-specific attributes (priority, sound, etc.)
- **manifest.json** - Integration metadata (domain: integration_blueprint, version: 0.1.0, iot_class: cloud_push)
- **translations/en.json** - UI strings for configuration flow and error messages

### Key Patterns

1. **Async-first**: All operations use async/await for API communication
2. **Legacy Notify Pattern**: Uses BaseNotificationService instead of NotifyEntity for compatibility
3. **Service Discovery**: Uses discovery.async_load_platform() to register notify service
4. **Error Handling**: Custom exceptions for auth, connection, and general API errors
5. **Flexible Configuration**: Supports API key and optional webhook URL

### Development Environment

- **Container**: VS Code devcontainer with Python 3.13
- **Home Assistant**: Local instance on port 8123 using config/configuration.yaml
- **Linting**: Ruff for formatting (line length 88) and code quality
- **Logging**: Debug level enabled for custom_components.integration_blueprint domain

## Integration Flow

1. User initiates config via UI (+ button → Custom Notifier)
2. ConfigFlow validates API key by testing connection
3. Successful validation creates config entry with API key and optional webhook URL
4. Integration loads and registers notify service via platform discovery
5. Service becomes available as notify.[configured_name]
6. Users can send notifications via service calls with message, title, and custom data

## Usage Example

```yaml
service: notify.custom_notifier
data:
  message: "This is a test notification"
  title: "Home Assistant Alert"
  data:
    priority: "high"
    sound: "notification"
    url: "https://example.com"
    url_title: "More Info"
    image: "https://example.com/image.png"
    actions:
      - action: "open"
        title: "Open App"
```

## Renaming the Integration

When creating your own notification integration from this template:

1. Replace all instances of `integration_blueprint` with your domain name
2. Update manifest.json with your integration details
3. Modify api.py to connect to your actual notification service
4. Update const.py with service-specific notification attributes
5. Customize translations/en.json with your integration's strings

## Important Implementation Details

- Uses legacy BaseNotificationService for broader compatibility
- Demo API endpoint (jsonplaceholder.typicode.com) should be replaced with actual service
- API key validation happens during config flow setup
- Notification service name is configurable by user
- No test suite included - consider adding pytest-homeassistant-custom-component
- Service is removed properly on integration unload