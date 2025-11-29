#!/usr/bin/env python3
"""
RelativityOne Security Audit Monitor

Monitors the Audit API for security-relevant events:
- Failed login attempts (brute force detection)
- Permission changes and elevations
- Large data exports (potential exfiltration)
- After-hours activity
- Lockbox modifications
- Suspicious user behavior

Critical for compliance and security monitoring.

Usage:
    python security_audit_monitor.py --config config.json
    python security_audit_monitor.py --config config.json --dry-run --verbose
"""

import argparse
import json
import logging
import os
import sys
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
from dateutil import parser as date_parser
from collections import defaultdict

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


# Alert levels with exit codes
ALERT_LEVELS = {
    "OK": 0,
    "WARNING": 1,
    "HIGH": 2,
    "CRITICAL": 3
}

# Security event categories
SECURITY_ACTIONS = {
    "login_failure": ["Login Failed", "Authentication Failed"],
    "login_success": ["Login", "Login Success"],
    "permission_change": ["Group Created", "Group Modified", "Group Deleted",
                         "User Added to Group", "User Removed from Group",
                         "Permission Changed", "Rights Modified"],
    "export": ["Export", "Download", "Production Export", "Mass Export"],
    "lockbox": ["Lockbox", "Lock Box"],
    "mass_operation": ["Mass Delete", "Mass Edit", "Mass Move", "Mass Copy"],
    "admin_action": ["System Setting Changed", "Configuration Modified",
                     "Agent Modified", "Script Executed"]
}

DEFAULT_CONFIG = {
    "relativity_host": "",
    "client_id": "",
    "client_secret": "",
    "username": "",
    "password": "",
    "auth_method": "bearer",
    "lookback_minutes": 15,
    "failed_login_warning": 5,
    "failed_login_high": 20,
    "failed_login_critical": 50,
    "export_docs_warning": 1000,
    "export_docs_high": 5000,
    "export_docs_critical": 10000,
    "business_hours_start": 7,
    "business_hours_end": 19,
    "alert_after_hours_exports": True,
    "notifications": {
        "email_enabled": False,
        "slack_enabled": False,
        "pagerduty_enabled": False,
        "teams_enabled": False,
        "webhook_enabled": False
    },
    "state_file": "/tmp/security_audit_state.json"
}


class RelativityAuth:
    """Handle RelativityOne authentication."""

    def __init__(self, config: Dict):
        self.config = config
        self._token = None
        self._token_expiry = None

    def get_bearer_token(self) -> str:
        """Get OAuth2 bearer token using client credentials flow."""
        token_url = f"{self.config['relativity_host']}/Relativity/Identity/connect/token"

        payload = {
            "grant_type": "client_credentials",
            "scope": "SystemUserInfo",
            "client_id": self.config["client_id"],
            "client_secret": self.config["client_secret"],
        }

        try:
            response = requests.post(token_url, data=payload, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            return token_data["access_token"]
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get bearer token: {e}")
            raise

    def get_auth_header(self) -> Dict[str, str]:
        """Get appropriate authorization header based on auth method."""
        if self.config.get("auth_method") == "bearer":
            token = self.get_bearer_token()
            return {"Authorization": f"Bearer {token}"}
        else:
            import base64
            credentials = base64.b64encode(
                f"{self.config['username']}:{self.config['password']}".encode()
            ).decode()
            return {"Authorization": f"Basic {credentials}"}


class SecurityAuditMonitor:
    """Monitor RelativityOne Security Audit Events."""

    def __init__(self, config: Dict, dry_run: bool = False, verbose: bool = False):
        self.config = {**DEFAULT_CONFIG, **config}
        self.dry_run = dry_run
        self.verbose = verbose
        self.auth = RelativityAuth(self.config)
        self.session = requests.Session()

        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def get_headers(self) -> Dict[str, str]:
        """Get standard headers for API requests."""
        return {
            **self.auth.get_auth_header(),
            "X-CSRF-Header": "-",
            "Content-Type": "application/json"
        }

    def query_audit_records(self) -> List[Dict]:
        """Query audit records from the Audit API."""
        url = f"{self.config['relativity_host']}/Relativity.REST/api/Relativity.Objects/workspace/-1/object/query"

        lookback = datetime.now(timezone.utc) - timedelta(minutes=self.config.get("lookback_minutes", 15))
        lookback_str = lookback.strftime("%Y-%m-%dT%H:%M:%SZ")

        payload = {
            "request": {
                "objectType": {"ArtifactTypeID": 1000026},  # Audit record
                "fields": [
                    {"Name": "Action"},
                    {"Name": "User Name"},
                    {"Name": "Timestamp"},
                    {"Name": "Details"},
                    {"Name": "Object Name"},
                    {"Name": "Workspace"},
                    {"Name": "Execution Time"}
                ],
                "condition": f"'Timestamp' >= '{lookback_str}'",
                "sorts": [{"FieldIdentifier": {"Name": "Timestamp"}, "Direction": "Descending"}],
                "queryHint": ""
            },
            "start": 0,
            "length": 1000
        }

        try:
            response = self.session.post(url, headers=self.get_headers(), json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("Objects", [])
        except requests.exceptions.RequestException as e:
            logging.warning(f"Failed to query audit records: {e}")
            # Try alternative audit endpoint
            return self.query_audit_alternative()

    def query_audit_alternative(self) -> List[Dict]:
        """Alternative method to query audit using different endpoint."""
        url = f"{self.config['relativity_host']}/Relativity.REST/api/relativity-audit/v1/workspaces/-1/audits"

        lookback = datetime.now(timezone.utc) - timedelta(minutes=self.config.get("lookback_minutes", 15))

        payload = {
            "request": {
                "startDate": lookback.isoformat(),
                "endDate": datetime.now(timezone.utc).isoformat(),
                "pageSize": 1000,
                "page": 1
            }
        }

        try:
            response = self.session.post(url, headers=self.get_headers(), json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("Data", [])
        except requests.exceptions.RequestException as e:
            logging.warning(f"Alternative audit query also failed: {e}")
            return []

    def extract_field_value(self, obj: Dict, field_name: str) -> Any:
        """Extract field value from Object Manager response."""
        # Handle direct field access (alternative API format)
        if field_name in obj:
            return obj[field_name]

        for field in obj.get("FieldValues", []):
            if field.get("Field", {}).get("Name") == field_name:
                value = field.get("Value")
                if isinstance(value, dict) and "Name" in value:
                    return value["Name"]
                if isinstance(value, dict) and "ArtifactID" in value:
                    return value.get("Name", str(value["ArtifactID"]))
                return value
        return None

    def categorize_event(self, action: str) -> Optional[str]:
        """Categorize an audit event by its action."""
        if not action:
            return None

        action_lower = action.lower()
        for category, keywords in SECURITY_ACTIONS.items():
            for keyword in keywords:
                if keyword.lower() in action_lower:
                    return category
        return None

    def is_after_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is outside business hours."""
        hour = timestamp.hour
        start = self.config.get("business_hours_start", 7)
        end = self.config.get("business_hours_end", 19)

        # Also check weekends
        if timestamp.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return True

        return hour < start or hour >= end

    def analyze_events(self, audit_records: List[Dict]) -> Dict[str, Any]:
        """Analyze audit records for security concerns."""
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_events": len(audit_records),
            "level": "OK",
            "alert_message": "",
            "alerts": [],
            "failed_logins": [],
            "failed_login_by_user": defaultdict(int),
            "failed_login_by_ip": defaultdict(int),
            "permission_changes": [],
            "large_exports": [],
            "after_hours_exports": [],
            "lockbox_changes": [],
            "mass_operations": []
        }

        for record in audit_records:
            action = self.extract_field_value(record, "Action") or ""
            user = self.extract_field_value(record, "User Name") or "Unknown"
            timestamp_str = self.extract_field_value(record, "Timestamp")
            details = self.extract_field_value(record, "Details") or ""
            obj_name = self.extract_field_value(record, "Object Name") or ""
            workspace = self.extract_field_value(record, "Workspace") or "Unknown"

            # Parse timestamp
            event_time = None
            if timestamp_str:
                try:
                    event_time = date_parser.parse(timestamp_str)
                    if event_time.tzinfo is None:
                        event_time = event_time.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            category = self.categorize_event(action)

            event_info = {
                "action": action,
                "user": user,
                "timestamp": timestamp_str,
                "details": details[:200] if details else "",
                "workspace": workspace,
                "object": obj_name
            }

            # Track failed logins
            if category == "login_failure":
                result["failed_logins"].append(event_info)
                result["failed_login_by_user"][user] += 1

            # Track permission changes
            elif category == "permission_change":
                result["permission_changes"].append(event_info)

            # Track exports
            elif category == "export":
                # Try to extract document count from details
                doc_count = 0
                if details:
                    import re
                    match = re.search(r'(\d+)\s*(documents?|docs?|items?)', details.lower())
                    if match:
                        doc_count = int(match.group(1))

                event_info["doc_count"] = doc_count

                # Check thresholds
                if doc_count >= self.config.get("export_docs_warning", 1000):
                    result["large_exports"].append(event_info)

                # Check after hours
                if event_time and self.is_after_hours(event_time):
                    if self.config.get("alert_after_hours_exports", True):
                        result["after_hours_exports"].append(event_info)

            # Track lockbox changes
            elif category == "lockbox":
                result["lockbox_changes"].append(event_info)

            # Track mass operations
            elif category == "mass_operation":
                result["mass_operations"].append(event_info)

        # Generate alerts and determine level
        self._evaluate_alerts(result)

        return result

    def _evaluate_alerts(self, result: Dict):
        """Evaluate results and generate alerts."""
        alerts = []
        max_level = "OK"

        # Check failed logins (brute force detection)
        total_failed = len(result["failed_logins"])
        critical_threshold = self.config.get("failed_login_critical", 50)
        high_threshold = self.config.get("failed_login_high", 20)
        warning_threshold = self.config.get("failed_login_warning", 5)

        if total_failed >= critical_threshold:
            max_level = "CRITICAL"
            # Find most targeted user
            if result["failed_login_by_user"]:
                top_user = max(result["failed_login_by_user"].items(), key=lambda x: x[1])
                alerts.append(f"BRUTE FORCE DETECTED: {total_failed} failed logins (top target: {top_user[0]} with {top_user[1]} attempts)")
        elif total_failed >= high_threshold:
            max_level = max(max_level, "HIGH", key=lambda x: ALERT_LEVELS.get(x, 0))
            alerts.append(f"Multiple failed logins: {total_failed} failures detected")
        elif total_failed >= warning_threshold:
            max_level = max(max_level, "WARNING", key=lambda x: ALERT_LEVELS.get(x, 0))
            alerts.append(f"Failed login activity: {total_failed} failures")

        # Check lockbox changes - always CRITICAL
        if result["lockbox_changes"]:
            max_level = "CRITICAL"
            alerts.append(f"LOCKBOX MODIFICATION: {len(result['lockbox_changes'])} lockbox changes detected!")

        # Check large exports
        export_critical = self.config.get("export_docs_critical", 10000)
        export_high = self.config.get("export_docs_high", 5000)

        for export in result["large_exports"]:
            if export["doc_count"] >= export_critical:
                max_level = "CRITICAL"
                alerts.append(f"LARGE EXPORT: {export['user']} exported {export['doc_count']} docs from {export['workspace']}")
            elif export["doc_count"] >= export_high:
                max_level = max(max_level, "HIGH", key=lambda x: ALERT_LEVELS.get(x, 0))
                alerts.append(f"Large export: {export['user']} exported {export['doc_count']} docs")

        # Check after-hours exports
        if result["after_hours_exports"]:
            max_level = max(max_level, "HIGH", key=lambda x: ALERT_LEVELS.get(x, 0))
            alerts.append(f"After-hours export activity: {len(result['after_hours_exports'])} exports outside business hours")

        # Check permission changes
        if len(result["permission_changes"]) >= 5:
            max_level = max(max_level, "WARNING", key=lambda x: ALERT_LEVELS.get(x, 0))
            alerts.append(f"Permission changes: {len(result['permission_changes'])} permission modifications")

        # Check mass operations
        if result["mass_operations"]:
            max_level = max(max_level, "HIGH", key=lambda x: ALERT_LEVELS.get(x, 0))
            for op in result["mass_operations"]:
                alerts.append(f"Mass operation: {op['action']} by {op['user']} in {op['workspace']}")

        result["level"] = max_level
        result["alerts"] = alerts

        if alerts:
            result["alert_message"] = "; ".join(alerts[:3])
            if len(alerts) > 3:
                result["alert_message"] += f" (+{len(alerts) - 3} more)"
        else:
            result["alert_message"] = f"No security concerns - {result['total_events']} audit events analyzed"

    def load_state(self) -> Dict:
        """Load previous state to prevent duplicate alerts."""
        state_file = self.config.get("state_file", "/tmp/security_audit_state.json")
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Could not load state file: {e}")
        return {}

    def save_state(self, state: Dict):
        """Save current state for future comparisons."""
        state_file = self.config.get("state_file", "/tmp/security_audit_state.json")
        try:
            simplified = {
                "level": state["level"],
                "alerts_count": len(state["alerts"]),
                "failed_logins": len(state["failed_logins"]),
                "timestamp": state["timestamp"]
            }
            with open(state_file, 'w') as f:
                json.dump(simplified, f, indent=2)
        except IOError as e:
            logging.warning(f"Could not save state file: {e}")

    def should_alert(self, result: Dict, previous_state: Dict) -> bool:
        """Determine if we should send an alert."""
        current_level = result["level"]
        previous_level = previous_state.get("level", "OK")

        # Always alert on CRITICAL
        if current_level == "CRITICAL":
            return True

        # Alert if level increased
        if ALERT_LEVELS.get(current_level, 0) > ALERT_LEVELS.get(previous_level, 0):
            return True

        # Always alert on HIGH for security events
        if current_level == "HIGH":
            return True

        # Alert on recovery
        if current_level == "OK" and previous_level != "OK":
            return True

        return False

    def send_email(self, result: Dict):
        """Send email notification."""
        notifications = self.config.get("notifications", {})
        if not notifications.get("email_enabled"):
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = notifications.get("email_from", "")
            msg['To'] = ", ".join(notifications.get("email_to", []))
            msg['Subject'] = f"[{result['level']}] RelativityOne SECURITY Alert"

            alerts_list = "\n".join([f"  - {a}" for a in result.get('alerts', [])]) or "  None"

            failed_logins = "\n".join([
                f"  - {l['user']}: {l['action']} at {l['timestamp']}"
                for l in result.get('failed_logins', [])[:10]
            ]) or "  None"

            body = f"""
RelativityOne Security Audit Monitor Alert

Level: {result['level']}
Message: {result['alert_message']}

SECURITY ALERTS:
{alerts_list}

SUMMARY:
- Total Events Analyzed: {result['total_events']}
- Failed Logins: {len(result.get('failed_logins', []))}
- Permission Changes: {len(result.get('permission_changes', []))}
- Large Exports: {len(result.get('large_exports', []))}
- After-Hours Exports: {len(result.get('after_hours_exports', []))}
- Lockbox Changes: {len(result.get('lockbox_changes', []))}
- Mass Operations: {len(result.get('mass_operations', []))}

RECENT FAILED LOGINS (up to 10):
{failed_logins}

Timestamp: {result['timestamp']}

---
This is an automated alert from the RelativityOne Security Audit Monitor.
See RUNBOOK-004 (Security Alerts) and RUNBOOK-009 (Audit & Compliance) for response procedures.
            """

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(
                notifications.get("smtp_server", ""),
                notifications.get("smtp_port", 587)
            )
            server.starttls()
            server.login(
                notifications.get("smtp_username", ""),
                notifications.get("smtp_password", "")
            )
            server.send_message(msg)
            server.quit()

            logging.info("Email notification sent successfully")

        except Exception as e:
            logging.error(f"Failed to send email: {e}")

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

        alerts_text = "\n".join(result.get('alerts', [])[:5]) or "None"

        payload = {
            "attachments": [{
                "color": color,
                "title": f"SECURITY Alert: {result['level']}",
                "text": result["alert_message"],
                "fields": [
                    {"title": "Failed Logins", "value": str(len(result.get("failed_logins", []))), "short": True},
                    {"title": "Large Exports", "value": str(len(result.get("large_exports", []))), "short": True},
                    {"title": "Lockbox Changes", "value": str(len(result.get("lockbox_changes", []))), "short": True},
                    {"title": "Mass Operations", "value": str(len(result.get("mass_operations", []))), "short": True}
                ],
                "footer": "RelativityOne Security Audit Monitor",
                "ts": int(datetime.now().timestamp())
            }]
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logging.info("Slack notification sent successfully")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send Slack notification: {e}")

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
            "dedup_key": "relativity-security-audit",
            "payload": {
                "summary": f"Security: {result['alert_message']}",
                "source": "RelativityOne Security Audit Monitor",
                "severity": severity,
                "custom_details": {
                    "alerts": result.get("alerts", []),
                    "failed_logins": len(result.get("failed_logins", [])),
                    "large_exports": len(result.get("large_exports", [])),
                    "lockbox_changes": len(result.get("lockbox_changes", []))
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
            logging.info(f"PagerDuty notification sent successfully ({event_action})")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send PagerDuty notification: {e}")

    def send_teams(self, result: Dict):
        """Send Microsoft Teams notification."""
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
            "summary": f"SECURITY Alert: {result['level']}",
            "sections": [{
                "activityTitle": f"SECURITY Alert: {result['level']}",
                "facts": [
                    {"name": "Message", "value": result["alert_message"]},
                    {"name": "Failed Logins", "value": str(len(result.get("failed_logins", [])))},
                    {"name": "Large Exports", "value": str(len(result.get("large_exports", [])))},
                    {"name": "Lockbox Changes", "value": str(len(result.get("lockbox_changes", [])))}
                ],
                "markdown": True
            }]
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logging.info("Teams notification sent successfully")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send Teams notification: {e}")

    def send_webhook(self, result: Dict):
        """Send generic webhook notification."""
        notifications = self.config.get("notifications", {})
        if not notifications.get("webhook_enabled"):
            return

        webhook_url = notifications.get("webhook_url", "")
        if not webhook_url:
            return

        payload = {
            "monitor": "security_audit_monitor",
            "level": result["level"],
            "alert_message": result["alert_message"],
            "details": {
                "alerts": result["alerts"],
                "failed_logins": len(result.get("failed_logins", [])),
                "permission_changes": len(result.get("permission_changes", [])),
                "large_exports": len(result.get("large_exports", [])),
                "lockbox_changes": len(result.get("lockbox_changes", []))
            },
            "timestamp": result["timestamp"]
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logging.info("Webhook notification sent successfully")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send webhook notification: {e}")

    def send_notifications(self, result: Dict):
        """Send all configured notifications."""
        if self.dry_run:
            logging.info(f"DRY RUN: Would send {result['level']} alert: {result['alert_message']}")
            return

        self.send_email(result)
        self.send_slack(result)
        self.send_pagerduty(result)
        self.send_teams(result)
        self.send_webhook(result)

    def run(self) -> int:
        """Main monitoring loop. Returns exit code based on alert level."""
        logging.info("Starting Security Audit monitoring check...")

        try:
            # Query audit records
            audit_records = self.query_audit_records()
            logging.info(f"Retrieved {len(audit_records)} audit records")

            # Analyze for security concerns
            result = self.analyze_events(audit_records)

            # Log the result
            logging.info(f"Security Status: {result['level']}")
            logging.info(f"Failed Logins: {len(result['failed_logins'])}")
            logging.info(f"Large Exports: {len(result['large_exports'])}")
            logging.info(f"Lockbox Changes: {len(result['lockbox_changes'])}")
            if result['alerts']:
                for alert in result['alerts']:
                    logging.info(f"ALERT: {alert}")

            # Check if we should alert
            previous_state = self.load_state()
            if self.should_alert(result, previous_state):
                logging.info(f"Sending {result['level']} alert...")
                self.send_notifications(result)
            else:
                logging.debug("No alert needed")

            # Save current state
            self.save_state(result)

            # Return exit code based on level
            return ALERT_LEVELS.get(result["level"], 0)

        except Exception as e:
            logging.error(f"Monitoring check failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 3  # CRITICAL


def load_config(config_path: Optional[str]) -> Dict:
    """Load configuration from file and/or environment variables."""
    config = DEFAULT_CONFIG.copy()

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = json.load(f)
            config.update(file_config)

    env_mappings = {
        "RELATIVITY_HOST": "relativity_host",
        "RELATIVITY_CLIENT_ID": "client_id",
        "RELATIVITY_CLIENT_SECRET": "client_secret",
        "RELATIVITY_USERNAME": "username",
        "RELATIVITY_PASSWORD": "password",
        "RELATIVITY_AUTH_METHOD": "auth_method",
    }

    for env_var, config_key in env_mappings.items():
        if os.environ.get(env_var):
            config[config_key] = os.environ[env_var]

    if os.environ.get("SLACK_ENABLED", "").lower() == "true":
        config.setdefault("notifications", {})["slack_enabled"] = True
    if os.environ.get("SLACK_WEBHOOK_URL"):
        config.setdefault("notifications", {})["slack_webhook_url"] = os.environ["SLACK_WEBHOOK_URL"]
    if os.environ.get("PAGERDUTY_ENABLED", "").lower() == "true":
        config.setdefault("notifications", {})["pagerduty_enabled"] = True
    if os.environ.get("PAGERDUTY_ROUTING_KEY"):
        config.setdefault("notifications", {})["pagerduty_routing_key"] = os.environ["PAGERDUTY_ROUTING_KEY"]

    return config


def main():
    parser = argparse.ArgumentParser(
        description="Monitor RelativityOne Security Audit Events"
    )
    parser.add_argument(
        "--config",
        help="Path to JSON config file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check only, don't send alerts"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    config = load_config(args.config)

    if not config.get("relativity_host"):
        print("ERROR: relativity_host is required")
        sys.exit(1)

    monitor = SecurityAuditMonitor(
        config=config,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    exit_code = monitor.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
