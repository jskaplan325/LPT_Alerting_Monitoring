#!/usr/bin/env python3
"""
SCOM Integration Module for RelativityOne Monitoring Scripts

This module provides Windows Event Log integration for Microsoft System Center
Operations Manager (SCOM) monitoring. Scripts write events to the Windows Event Log,
which SCOM monitors and processes according to configured rules.

Event Sources:
    - RelativityOne-Monitor: All RelativityOne monitoring events
    - RevealAI-Monitor: All Reveal AI monitoring events

Event ID Ranges:
    - 1000-1099: Telemetry Agent events
    - 1100-1199: Billing Agent events
    - 1200-1299: Worker Health events
    - 1300-1399: Job Queue events
    - 1400-1499: Security Audit events
    - 1500-1599: Alert Manager events
    - 1600-1699: aiR for Review events
    - 1700-1799: aiR for Privilege events
    - 2000-2099: Reveal AI API Health events
    - 2100-2199: Reveal AI Job events
    - 2200-2299: Reveal AI Export events

Event Types (matching SCOM severity):
    - EVENTLOG_INFORMATION_TYPE (0): OK status
    - EVENTLOG_WARNING_TYPE (1): WARNING status
    - EVENTLOG_ERROR_TYPE (2): HIGH/CRITICAL status

Requirements:
    pip install pywin32  (Windows only)

Usage:
    from scom_integration import SCOMIntegration

    scom = SCOMIntegration(config, logger)
    scom.write_event(
        event_id=1001,
        level="CRITICAL",
        message="Telemetry agent not responding",
        details={"agent_name": "Telemetry", "status": "Not Responding"}
    )
"""

import os
import sys
import json
import logging
import platform
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Windows Event Log constants (used even on non-Windows for config)
EVENTLOG_SUCCESS = 0
EVENTLOG_ERROR_TYPE = 1
EVENTLOG_WARNING_TYPE = 2
EVENTLOG_INFORMATION_TYPE = 4
EVENTLOG_AUDIT_SUCCESS = 8
EVENTLOG_AUDIT_FAILURE = 16


# =============================================================================
# EVENT ID MAPPINGS
# =============================================================================

EVENT_SOURCES = {
    "relativity": "RelativityOne-Monitor",
    "reveal": "RevealAI-Monitor",
}

# Event ID ranges by monitor type
EVENT_ID_BASE = {
    # RelativityOne monitors
    "telemetry_agent": 1000,
    "billing_agent": 1100,
    "worker_health": 1200,
    "job_queue": 1300,
    "security_audit": 1400,
    "alert_manager": 1500,
    # RelativityOne aiR monitors
    "air_review": 1600,
    "air_privilege": 1700,
    "air_job": 1600,  # Alias for combined aiR monitor
    # Reveal AI monitors
    "reveal_api_health": 2000,
    "reveal_job": 2100,
    "reveal_export": 2200,
}

# Event ID offsets by alert level
EVENT_LEVEL_OFFSET = {
    "OK": 0,
    "INFO": 1,
    "WARNING": 2,
    "HIGH": 3,
    "CRITICAL": 4,
    "AUDIT": 5,
}


# =============================================================================
# SCOM INTEGRATION CLASS
# =============================================================================

class SCOMIntegration:
    """
    Handles SCOM integration via Windows Event Log.

    On Windows: Writes to Windows Event Log
    On Linux/Mac: Writes to syslog or file (for testing/development)
    """

    def __init__(self, config: Dict, logger: logging.Logger, monitor_type: str, platform_type: str = "relativity"):
        """
        Initialize SCOM integration.

        Args:
            config: Configuration dictionary with SCOM settings
            logger: Python logger instance
            monitor_type: Type of monitor (e.g., "telemetry_agent", "reveal_job")
            platform_type: "relativity" or "reveal"
        """
        self.config = config
        self.logger = logger
        self.monitor_type = monitor_type
        self.platform_type = platform_type
        self.enabled = config.get("scom_enabled", False)
        self.event_source = EVENT_SOURCES.get(platform_type, "RelativityOne-Monitor")
        self.event_id_base = EVENT_ID_BASE.get(monitor_type, 1000)
        self.is_windows = platform.system() == "Windows"

        # Windows Event Log handle
        self._win32_available = False
        self._event_log_handle = None

        if self.enabled and self.is_windows:
            self._init_windows_event_log()

    def _init_windows_event_log(self):
        """Initialize Windows Event Log."""
        try:
            import win32evtlogutil
            import win32evtlog
            import win32con

            self._win32_available = True
            self._win32evtlogutil = win32evtlogutil
            self._win32evtlog = win32evtlog
            self._win32con = win32con

            # Register the event source if not already registered
            try:
                win32evtlogutil.AddSourceToRegistry(
                    self.event_source,
                    msgDLL=None,
                    eventLogType="Application",
                    eventLogFlags=None
                )
            except Exception:
                # Source may already be registered
                pass

            self.logger.info(f"SCOM integration initialized - Event Source: {self.event_source}")

        except ImportError:
            self.logger.warning("pywin32 not installed. Install with: pip install pywin32")
            self._win32_available = False

    def get_event_id(self, level: str) -> int:
        """
        Get the event ID for a given alert level.

        Args:
            level: Alert level (OK, WARNING, HIGH, CRITICAL)

        Returns:
            Event ID integer
        """
        offset = EVENT_LEVEL_OFFSET.get(level.upper(), 0)
        return self.event_id_base + offset

    def get_event_type(self, level: str) -> int:
        """
        Map alert level to Windows Event Log type.

        Args:
            level: Alert level

        Returns:
            Windows Event Log type constant
        """
        level_upper = level.upper()
        if level_upper in ["CRITICAL", "HIGH"]:
            return EVENTLOG_ERROR_TYPE
        elif level_upper in ["WARNING"]:
            return EVENTLOG_WARNING_TYPE
        else:
            return EVENTLOG_INFORMATION_TYPE

    def write_event(self, level: str, message: str, details: Optional[Dict[str, Any]] = None,
                    event_id: Optional[int] = None):
        """
        Write an event to Windows Event Log for SCOM monitoring.

        Args:
            level: Alert level (OK, WARNING, HIGH, CRITICAL)
            message: Event message
            details: Additional details dictionary
            event_id: Optional specific event ID (otherwise calculated from level)
        """
        if not self.enabled:
            self.logger.debug("SCOM integration disabled - skipping event write")
            return

        # Calculate event ID if not provided
        if event_id is None:
            event_id = self.get_event_id(level)

        event_type = self.get_event_type(level)

        # Format the event data
        event_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "monitor": self.monitor_type,
            "platform": self.platform_type,
            "level": level,
            "message": message,
        }
        if details:
            event_data["details"] = details

        event_strings = [
            f"Level: {level}",
            f"Monitor: {self.monitor_type}",
            f"Message: {message}",
            f"Details: {json.dumps(details) if details else 'N/A'}",
            f"Timestamp: {event_data['timestamp']}",
        ]

        if self.is_windows and self._win32_available:
            self._write_windows_event(event_id, event_type, event_strings)
        else:
            self._write_fallback_event(event_id, event_type, event_strings, event_data)

    def _write_windows_event(self, event_id: int, event_type: int, event_strings: list):
        """Write event to Windows Event Log."""
        try:
            self._win32evtlogutil.ReportEvent(
                self.event_source,
                event_id,
                eventCategory=0,
                eventType=event_type,
                strings=event_strings,
                data=None
            )
            self.logger.info(f"SCOM event written - ID: {event_id}, Source: {self.event_source}")
        except Exception as e:
            self.logger.error(f"Failed to write Windows Event Log: {e}")

    def _write_fallback_event(self, event_id: int, event_type: int, event_strings: list, event_data: dict):
        """
        Fallback event writing for non-Windows or when pywin32 is unavailable.
        Writes to a JSON file that can be monitored.
        """
        fallback_file = self.config.get("scom_fallback_file", "/var/log/scom_events.json")

        event_record = {
            "event_id": event_id,
            "event_type": event_type,
            "event_source": self.event_source,
            "strings": event_strings,
            "data": event_data,
        }

        try:
            # Append to JSON lines file
            with open(fallback_file, "a") as f:
                f.write(json.dumps(event_record) + "\n")
            self.logger.info(f"SCOM event written to fallback file: {fallback_file}")
        except Exception as e:
            self.logger.warning(f"Failed to write fallback event: {e}")
            # Log the event data instead
            self.logger.info(f"SCOM Event (not written): {json.dumps(event_data)}")

    def write_check_result(self, check_result: Dict[str, Any]):
        """
        Write a monitoring check result to SCOM.

        Args:
            check_result: Dictionary containing level, message, details, etc.
        """
        level = check_result.get("level", "UNKNOWN")
        message = check_result.get("message", "Unknown status")

        # Extract relevant details
        details = {
            k: v for k, v in check_result.items()
            if k not in ["level", "message"] and v is not None
        }

        self.write_event(level=level, message=message, details=details)

    def resolve_alert(self, message: str = "Alert resolved"):
        """
        Write an OK event to indicate alert resolution.

        Args:
            message: Resolution message
        """
        self.write_event(level="OK", message=message)


# =============================================================================
# SCOM CONFIGURATION TEMPLATE
# =============================================================================

SCOM_CONFIG_TEMPLATE = {
    "_comment_scom": "SCOM Integration Settings",
    "scom_enabled": True,
    "scom_fallback_file": "/var/log/scom_events.json",
}


def get_scom_config_template() -> Dict:
    """Get the SCOM configuration template for inclusion in config files."""
    return SCOM_CONFIG_TEMPLATE.copy()


# =============================================================================
# POWERSHELL HELPER FOR EVENT SOURCE REGISTRATION
# =============================================================================

POWERSHELL_REGISTER_SOURCES = '''
# PowerShell script to register SCOM event sources
# Run as Administrator

$sources = @(
    "RelativityOne-Monitor",
    "RevealAI-Monitor"
)

foreach ($source in $sources) {
    if (-not [System.Diagnostics.EventLog]::SourceExists($source)) {
        [System.Diagnostics.EventLog]::CreateEventSource($source, "Application")
        Write-Host "Created event source: $source"
    } else {
        Write-Host "Event source already exists: $source"
    }
}

Write-Host "Event source registration complete."
'''


def print_powershell_setup():
    """Print PowerShell script to register event sources."""
    print("=" * 60)
    print("SCOM Event Source Registration Script")
    print("Run this PowerShell script as Administrator on monitoring servers")
    print("=" * 60)
    print(POWERSHELL_REGISTER_SOURCES)


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SCOM Integration Module")
    parser.add_argument("--setup", action="store_true", help="Print PowerShell setup script")
    parser.add_argument("--test", action="store_true", help="Test event writing")
    args = parser.parse_args()

    if args.setup:
        print_powershell_setup()
    elif args.test:
        # Test mode
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger("SCOMTest")

        config = {
            "scom_enabled": True,
            "scom_fallback_file": "/tmp/scom_test_events.json",
        }

        scom = SCOMIntegration(config, logger, "telemetry_agent", "relativity")

        print("Testing SCOM integration...")
        scom.write_event("OK", "Test OK event", {"test": True})
        scom.write_event("WARNING", "Test WARNING event", {"test": True})
        scom.write_event("CRITICAL", "Test CRITICAL event", {"test": True})

        print(f"\nEvents written. Check: {config['scom_fallback_file']}")
    else:
        parser.print_help()
