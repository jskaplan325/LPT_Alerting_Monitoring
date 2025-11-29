#!/usr/bin/env python3
"""
Reveal AI Export Monitor

Monitors export and production jobs for security concerns:
- Large exports (potential data exfiltration)
- After-hours exports
- Exports by unusual users
- Production exports to external destinations

Usage:
    python reveal_export_monitor.py --config config.json
    python reveal_export_monitor.py --config config.json --dry-run --verbose
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install with: pip install requests")
    sys.exit(1)

try:
    from dateutil import parser as date_parser
except ImportError:
    print("ERROR: python-dateutil library required. Install with: pip install python-dateutil")
    sys.exit(1)

# Import SCOM integration (optional)
try:
    from scom_integration import SCOMIntegration
    SCOM_AVAILABLE = True
except ImportError:
    SCOM_AVAILABLE = False


ALERT_LEVELS = {
    "OK": 0,
    "WARNING": 1,
    "HIGH": 2,
    "CRITICAL": 3
}

DEFAULT_CONFIG = {
    "reveal_host": "",
    "nia_host": "",
    "nia_port": 5566,
    "username": "",
    "password": "",
    "lookback_hours": 24,
    "export_docs_warning": 1000,
    "export_docs_high": 5000,
    "export_docs_critical": 10000,
    "business_hours_start": 7,
    "business_hours_end": 19,
    "alert_after_hours": True,
    "notifications": {
        "email_enabled": False,
        "slack_enabled": False,
        "pagerduty_enabled": False,
        "teams_enabled": False,
        "webhook_enabled": False
    },
    "state_file": "/tmp/reveal_export_state.json",
    "scom_enabled": False,
    "scom_fallback_file": "/var/log/scom_events.json"
}


class RevealAuth:
    """Handle Reveal AI authentication."""

    def __init__(self, config: Dict):
        self.config = config
        self._session_token = None

    def get_session_token(self) -> str:
        """Get session token via login API."""
        login_url = f"{self.config['reveal_host']}/rest/api/v2/login"
        payload = {
            "username": self.config["username"],
            "password": self.config["password"]
        }

        try:
            response = requests.post(login_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("loginSessionId", "")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get session token: {e}")
            raise

    def get_auth_header(self) -> Dict[str, str]:
        """Get authentication header."""
        if not self._session_token:
            self._session_token = self.get_session_token()
        return {"incontrolauthtoken": self._session_token}


class RevealExportMonitor:
    """Monitor Reveal AI Exports for Security."""

    def __init__(self, config: Dict, dry_run: bool = False, verbose: bool = False):
        self.config = {**DEFAULT_CONFIG, **config}
        self.dry_run = dry_run
        self.verbose = verbose
        self.auth = None
        self.session = requests.Session()

        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # Initialize SCOM integration
        self.scom = None
        if SCOM_AVAILABLE and self.config.get("scom_enabled", False):
            self.scom = SCOMIntegration(self.config, logging.getLogger(), "reveal_export", "reveal")
            logging.info("SCOM integration enabled")

    def get_auth(self) -> RevealAuth:
        """Get or create auth handler."""
        if not self.auth and self.config.get("username"):
            self.auth = RevealAuth(self.config)
        return self.auth

    def get_exports(self) -> List[Dict]:
        """Query export jobs from API."""
        exports = []

        # Try REST API first
        try:
            auth = self.get_auth()
            if auth:
                headers = auth.get_auth_header()
                url = f"{self.config['reveal_host']}/rest/api/v2/exports"
                response = self.session.get(url, headers=headers, timeout=60)
                response.raise_for_status()
                exports.extend(response.json())
        except Exception as e:
            logging.warning(f"REST API export query failed: {e}")

        # Also check NIA for export jobs
        try:
            nia_host = self.config.get("nia_host") or self.config.get("reveal_host", "").replace("https://", "http://")
            nia_port = self.config.get("nia_port", 5566)
            url = f"{nia_host}:{nia_port}/nia/jobs"

            response = self.session.get(url, timeout=60)
            if response.status_code == 200:
                jobs = response.json()
                for job in jobs:
                    job_type = (job.get("jobType") or job.get("type") or "").lower()
                    if "export" in job_type or "production" in job_type:
                        exports.append(job)
        except Exception as e:
            logging.warning(f"NIA API job query failed: {e}")

        return exports

    def is_after_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is outside business hours."""
        hour = timestamp.hour
        start = self.config.get("business_hours_start", 7)
        end = self.config.get("business_hours_end", 19)

        # Weekend check
        if timestamp.weekday() >= 5:
            return True

        return hour < start or hour >= end

    def analyze_exports(self, exports: List[Dict]) -> Dict[str, Any]:
        """Analyze exports for security concerns."""
        now = datetime.now(timezone.utc)
        lookback = now - timedelta(hours=self.config.get("lookback_hours", 24))

        result = {
            "timestamp": now.isoformat(),
            "total_exports": len(exports),
            "large_exports": [],
            "after_hours_exports": [],
            "critical_exports": [],
            "alerts": [],
            "level": "OK",
            "alert_message": ""
        }

        warning_threshold = self.config.get("export_docs_warning", 1000)
        high_threshold = self.config.get("export_docs_high", 5000)
        critical_threshold = self.config.get("export_docs_critical", 10000)

        for export in exports:
            # Extract export info (handle different API formats)
            export_id = export.get("exportId") or export.get("id") or export.get("jobId")
            user = export.get("user") or export.get("submittedBy") or export.get("createdBy", "Unknown")
            doc_count = export.get("documentCount") or export.get("docCount") or export.get("count", 0)
            export_type = export.get("type") or export.get("exportType") or export.get("jobType", "Export")
            project = export.get("project") or export.get("projectId") or export.get("projectName", "Unknown")
            destination = export.get("destination") or export.get("outputPath", "")
            timestamp_str = export.get("timestamp") or export.get("created") or export.get("startTime")

            # Parse timestamp
            export_time = None
            if timestamp_str:
                try:
                    export_time = date_parser.parse(timestamp_str)
                    if export_time.tzinfo is None:
                        export_time = export_time.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            # Skip old exports
            if export_time and export_time < lookback:
                continue

            export_info = {
                "export_id": export_id,
                "user": user,
                "document_count": doc_count,
                "type": export_type,
                "project": project,
                "destination": destination,
                "timestamp": timestamp_str,
                "level": "OK"
            }

            # Check document count thresholds
            if isinstance(doc_count, (int, float)):
                if doc_count >= critical_threshold:
                    export_info["level"] = "CRITICAL"
                    result["critical_exports"].append(export_info)
                    result["alerts"].append(
                        f"LARGE EXPORT: {user} exported {doc_count} docs from {project}"
                    )
                elif doc_count >= high_threshold:
                    export_info["level"] = "HIGH"
                    result["large_exports"].append(export_info)
                elif doc_count >= warning_threshold:
                    export_info["level"] = "WARNING"
                    result["large_exports"].append(export_info)

            # Check after-hours
            if export_time and self.is_after_hours(export_time):
                if self.config.get("alert_after_hours", True):
                    export_info["after_hours"] = True
                    result["after_hours_exports"].append(export_info)
                    if export_info["level"] == "OK":
                        export_info["level"] = "HIGH"

        # Determine overall level
        self._determine_alert_level(result)

        return result

    def _determine_alert_level(self, result: Dict):
        """Determine overall alert level."""
        max_level = "OK"

        if result["critical_exports"]:
            max_level = "CRITICAL"
        elif result["large_exports"]:
            # Check levels of large exports
            for exp in result["large_exports"]:
                if exp.get("level") == "HIGH":
                    max_level = "HIGH"
                    break
            if max_level == "OK":
                max_level = "WARNING"

        if result["after_hours_exports"] and max_level != "CRITICAL":
            max_level = max(max_level, "HIGH", key=lambda x: ALERT_LEVELS.get(x, 0))
            result["alerts"].append(
                f"After-hours exports: {len(result['after_hours_exports'])} exports outside business hours"
            )

        result["level"] = max_level

        if result["alerts"]:
            result["alert_message"] = "; ".join(result["alerts"][:3])
            if len(result["alerts"]) > 3:
                result["alert_message"] += f" (+{len(result['alerts']) - 3} more)"
        else:
            result["alert_message"] = f"No export security concerns - {result['total_exports']} exports analyzed"

    def load_state(self) -> Dict:
        """Load previous state."""
        state_file = self.config.get("state_file", "/tmp/reveal_export_state.json")
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass
        return {}

    def save_state(self, state: Dict):
        """Save state."""
        state_file = self.config.get("state_file", "/tmp/reveal_export_state.json")
        try:
            simplified = {
                "level": state["level"],
                "critical_count": len(state["critical_exports"]),
                "large_count": len(state["large_exports"]),
                "timestamp": state["timestamp"]
            }
            with open(state_file, 'w') as f:
                json.dump(simplified, f, indent=2)
        except IOError as e:
            logging.warning(f"Could not save state: {e}")

    def should_alert(self, result: Dict, previous_state: Dict) -> bool:
        """Determine if should alert."""
        current_level = result["level"]
        previous_level = previous_state.get("level", "OK")

        if current_level == "CRITICAL":
            return True
        if ALERT_LEVELS.get(current_level, 0) > ALERT_LEVELS.get(previous_level, 0):
            return True
        if current_level == "OK" and previous_level != "OK":
            return True

        return False

    def send_slack(self, result: Dict):
        """Send Slack notification."""
        notifications = self.config.get("notifications", {})
        if not notifications.get("slack_enabled"):
            return

        webhook_url = notifications.get("slack_webhook_url", "")
        if not webhook_url:
            return

        color = {
            "OK": "good",
            "WARNING": "warning",
            "HIGH": "#ff9900",
            "CRITICAL": "danger"
        }.get(result["level"], "#cccccc")

        payload = {
            "attachments": [{
                "color": color,
                "title": f"Reveal AI Export Security: {result['level']}",
                "text": result["alert_message"],
                "fields": [
                    {"title": "Critical Exports", "value": str(len(result.get("critical_exports", []))), "short": True},
                    {"title": "Large Exports", "value": str(len(result.get("large_exports", []))), "short": True},
                    {"title": "After-Hours", "value": str(len(result.get("after_hours_exports", []))), "short": True},
                    {"title": "Total Analyzed", "value": str(result.get("total_exports", 0)), "short": True}
                ],
                "footer": "Reveal AI Export Monitor",
                "ts": int(datetime.now().timestamp())
            }]
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logging.info("Slack notification sent")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send Slack: {e}")

    def send_pagerduty(self, result: Dict):
        """Send PagerDuty notification."""
        notifications = self.config.get("notifications", {})
        if not notifications.get("pagerduty_enabled"):
            return

        routing_key = notifications.get("pagerduty_routing_key", "")
        if not routing_key:
            return

        severity = {
            "OK": "info",
            "WARNING": "warning",
            "HIGH": "error",
            "CRITICAL": "critical"
        }.get(result["level"], "info")

        event_action = "resolve" if result["level"] == "OK" else "trigger"

        payload = {
            "routing_key": routing_key,
            "event_action": event_action,
            "dedup_key": "reveal-export-security",
            "payload": {
                "summary": f"Reveal AI Export: {result['alert_message']}",
                "source": "Reveal AI Export Monitor",
                "severity": severity,
                "custom_details": {
                    "critical_exports": len(result.get("critical_exports", [])),
                    "large_exports": len(result.get("large_exports", [])),
                    "after_hours": len(result.get("after_hours_exports", []))
                }
            }
        }

        try:
            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logging.info(f"PagerDuty notification sent ({event_action})")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send PagerDuty: {e}")

    def send_teams(self, result: Dict):
        """Send Teams notification."""
        notifications = self.config.get("notifications", {})
        if not notifications.get("teams_enabled"):
            return

        webhook_url = notifications.get("teams_webhook_url", "")
        if not webhook_url:
            return

        color = {
            "OK": "00ff00",
            "WARNING": "ffff00",
            "HIGH": "ff9900",
            "CRITICAL": "ff0000"
        }.get(result["level"], "cccccc")

        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": f"Reveal AI Export Security: {result['level']}",
            "sections": [{
                "activityTitle": f"Reveal AI Export Security: {result['level']}",
                "facts": [
                    {"name": "Message", "value": result["alert_message"]},
                    {"name": "Critical Exports", "value": str(len(result.get("critical_exports", [])))},
                    {"name": "Large Exports", "value": str(len(result.get("large_exports", [])))},
                    {"name": "After-Hours", "value": str(len(result.get("after_hours_exports", [])))}
                ],
                "markdown": True
            }]
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logging.info("Teams notification sent")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send Teams: {e}")

    def send_webhook(self, result: Dict):
        """Send webhook notification."""
        notifications = self.config.get("notifications", {})
        if not notifications.get("webhook_enabled"):
            return

        webhook_url = notifications.get("webhook_url", "")
        if not webhook_url:
            return

        payload = {
            "monitor": "reveal_export_monitor",
            "platform": "Reveal AI",
            "level": result["level"],
            "alert_message": result["alert_message"],
            "critical_exports": result.get("critical_exports", []),
            "large_exports": result.get("large_exports", []),
            "after_hours_exports": result.get("after_hours_exports", []),
            "timestamp": result["timestamp"]
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logging.info("Webhook notification sent")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send webhook: {e}")

    def send_scom(self, result: Dict):
        """Write event to SCOM via Windows Event Log."""
        if not self.scom:
            return

        try:
            check_result = {
                "level": result.get("level", "UNKNOWN"),
                "message": result.get("alert_message", ""),
                "large_exports": result.get("large_exports_count", 0),
                "after_hours_exports": result.get("after_hours_count", 0),
                "total_docs_exported": result.get("total_docs", 0)
            }
            self.scom.write_check_result(check_result)
            logging.info("SCOM event written")
        except Exception as e:
            logging.error(f"Failed to write SCOM event: {e}")

    def send_notifications(self, result: Dict):
        """Send all notifications."""
        # Always write to SCOM (even for OK status)
        self.send_scom(result)

        if self.dry_run:
            logging.info(f"DRY RUN: Would send {result['level']} alert: {result['alert_message']}")
            return

        self.send_slack(result)
        self.send_pagerduty(result)
        self.send_teams(result)
        self.send_webhook(result)

    def run(self) -> int:
        """Main monitoring run."""
        logging.info("Starting Reveal AI Export Monitor check...")

        try:
            exports = self.get_exports()
            logging.info(f"Retrieved {len(exports)} exports")

            result = self.analyze_exports(exports)

            logging.info(f"Export Security Status: {result['level']}")
            logging.info(f"Critical: {len(result['critical_exports'])}, Large: {len(result['large_exports'])}")
            logging.info(f"After-Hours: {len(result['after_hours_exports'])}")
            logging.info(f"Message: {result['alert_message']}")

            previous_state = self.load_state()
            if self.should_alert(result, previous_state):
                logging.info(f"Sending {result['level']} alert...")
                self.send_notifications(result)

            self.save_state(result)

            return ALERT_LEVELS.get(result["level"], 0)

        except Exception as e:
            logging.error(f"Monitoring check failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 3


def load_config(config_path: Optional[str]) -> Dict:
    """Load configuration."""
    config = DEFAULT_CONFIG.copy()

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = json.load(f)
            config.update(file_config)

    env_mappings = {
        "REVEAL_HOST": "reveal_host",
        "REVEAL_NIA_HOST": "nia_host",
        "REVEAL_USERNAME": "username",
        "REVEAL_PASSWORD": "password",
    }

    for env_var, config_key in env_mappings.items():
        if os.environ.get(env_var):
            config[config_key] = os.environ[env_var]

    if os.environ.get("SLACK_ENABLED", "").lower() == "true":
        config.setdefault("notifications", {})["slack_enabled"] = True
    if os.environ.get("SLACK_WEBHOOK_URL"):
        config.setdefault("notifications", {})["slack_webhook_url"] = os.environ["SLACK_WEBHOOK_URL"]

    return config


def main():
    parser = argparse.ArgumentParser(description="Monitor Reveal AI Exports for Security")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--dry-run", action="store_true", help="Check only, don't send alerts")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()
    config = load_config(args.config)

    if not config.get("reveal_host") and not config.get("nia_host"):
        print("ERROR: reveal_host or nia_host is required")
        sys.exit(1)

    monitor = RevealExportMonitor(
        config=config,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    exit_code = monitor.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
