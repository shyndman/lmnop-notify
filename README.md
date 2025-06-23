# LMNOP Notifier

A custom Home Assistant notification integration tailored for our house and preferences.

## What is this?

This is a notification pipeline designed specifically for our household's needs. It provides priority-based notifications with visual RGB light alerts for important messages.

## Features (Planned)

- Priority-based notifications (CRITICAL, HIGH, MEDIUM, LOW, DEBUG)
- RGB light alerts for HIGH and CRITICAL notifications
- Persistent notification tracking with acknowledgment
- Light state restoration after alerts are dismissed

## Status

This integration is currently in early development. Core notification infrastructure is in place, but most features are not yet implemented.

## Development

```bash
# Setup development environment
./scripts/setup

# Start local Home Assistant with debug logging
./scripts/develop

# Lint and format code
./scripts/lint
```

## Installation

This integration is not ready for general use and is specifically designed for our house. It is not intended for distribution or use by others.