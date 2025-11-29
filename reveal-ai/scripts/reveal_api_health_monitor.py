#!/usr/bin/env python3
"""
Reveal AI API Health Monitor

Monitors the NIA API health endpoint for availability and response time.
If the API is down, ALL Reveal AI operations are affected.

Usage:
    python reveal_api_health_monitor.py --config config.json
    python reveal_api_health_monitor.py --config config.json --dry-run --verbose
"""

import argparse
import json
import logging
import os
import sys
import smtplib
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install with: pip install requests")
    sys.exit(1)


# Alert levels with exit codes
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
    "timeout_seconds": 10,
    "response_time_warning_ms": 2000,
    "response_time_high_ms": 5000,
    "response_time_critical_ms": 10000,
    "consecutive_failures_critical": 3,
    "notifications": {
        "email_enabled": False,
        "slack_enabled": False,
        "pagerduty_enabled": False,
        "teams_enabled": False,
        "webhook_enabled": False
    },
    "state_file": "/tmp/reveal_api_health_state.json"
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
        """Get authentication header for API requests."""
        if not self._session_token:
            self._session_token = self.get_session_token()
        return {"incontrolauthtoken": self._session_token}


class RevealAPIHealthMonitor:
    """Monitor Reveal AI API Health."""

    def __init__(self, config: Dict, dry_run: bool = False, verbose: bool = False):
        self.config = {**DEFAULT_CONFIG, **config}
        self.dry_run = dry_run
        self.verbose = verbose
        self.session = requests.Session()

        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def check_nia_health(self) -> Dict[str, Any]:
        """Check NIA API health endpoint."""
        nia_host = self.config.get("nia_host") or self.config.get("reveal_host", "").replace("https://", "http://")
        nia_port = self.config.get("nia_port", 5566)
        url = f"{nia_host}:{nia_port}/nia/version"

        result = {
            "endpoint": "NIA API",
            "url": url,
            "status": "Unknown",
            "response_code": None,
            "response_time_ms": None,
            "error": None
        }

        try:
            start_time = time.time()
            response = self.session.get(
                url,
                timeout=self.config.get("timeout_seconds", 10)
            )
            response_time = (time.time() - start_time) * 1000

            result["response_code"] = response.status_code
            result["response_time_ms"] = round(response_time, 2)

            if response.status_code == 200:
                result["status"] = "Healthy"
                try:
                    result["version"] = response.json()
                except:
                    result["version"] = response.text[:100]
            else:
                result["status"] = "Unhealthy"
                result["error"] = f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            result["status"] = "Timeout"
            result["error"] = "Connection timed out"
        except requests.exceptions.ConnectionError as e:
            result["status"] = "Connection Error"
            result["error"] = str(e)[:200]
        except Exception as e:
            result["status"] = "Error"
            result["error"] = str(e)[:200]

        return result

    def check_rest_api_health(self) -> Dict[str, Any]:
        """Check REST API v2 health."""
        url = f"{self.config['reveal_host']}/rest/api/v2/health"

        result = {
            "endpoint": "REST API v2",
            "url": url,
            "status": "Unknown",
            "response_code": None,
            "response_time_ms": None,
            "error": None
        }

        try:
            start_time = time.time()
            response = self.session.get(
                url,
                timeout=self.config.get("timeout_seconds", 10)
            )
            response_time = (time.time() - start_time) * 1000

            result["response_code"] = response.status_code
            result["response_time_ms"] = round(response_time, 2)

            if response.status_code == 200:
                result["status"] = "Healthy"
            else:
                result["status"] = "Unhealthy"
                result["error"] = f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            result["status"] = "Timeout"
            result["error"] = "Connection timed out"
        except requests.exceptions.ConnectionError as e:
            result["status"] = "Connection Error"
            result["error"] = str(e)[:200]
        except Exception as e:
            result["status"] = "Error"
            result["error"] = str(e)[:200]

        return result

    def analyze_health(self, nia_result: Dict, rest_result: Dict) -> Dict[str, Any]:
        """Analyze health check results and determine alert level."""
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nia_api": nia_result,
            "rest_api": rest_result,
            "level": "OK",
            "alert_message": "",
            "all_healthy": True
        }

        issues = []

        # Check NIA API
        if nia_result["status"] != "Healthy":
            result["all_healthy"] = False
            issues.append(f"NIA API: {nia_result['status']} - {nia_result.get('error', 'Unknown error')}")

        # Check REST API
        if rest_result["status"] != "Healthy":
            result["all_healthy"] = False
            issues.append(f"REST API: {rest_result['status']} - {rest_result.get('error', 'Unknown error')}")

        # Check response times
        critical_ms = self.config.get("response_time_critical_ms", 10000)
        high_ms = self.config.get("response_time_high_ms", 5000)
        warning_ms = self.config.get("response_time_warning_ms", 2000)

        for check in [nia_result, rest_result]:
            if check.get("response_time_ms"):
                if check["response_time_ms"] >= critical_ms:
                    issues.append(f"{check['endpoint']} slow: {check['response_time_ms']}ms")

        # Determine alert level
        if not result["all_healthy"]:
            # Any API down is CRITICAL
            result["level"] = "CRITICAL"
            result["alert_message"] = f"API HEALTH FAILURE: {'; '.join(issues)}"
        elif any(c.get("response_time_ms", 0) >= critical_ms for c in [nia_result, rest_result] if c.get("response_time_ms")):
            result["level"] = "CRITICAL"
            result["alert_message"] = f"API response time critical: {'; '.join(issues)}"
        elif any(c.get("response_time_ms", 0) >= high_ms for c in [nia_result, rest_result] if c.get("response_time_ms")):
            result["level"] = "HIGH"
            result["alert_message"] = "API response time high - investigate performance"
        elif any(c.get("response_time_ms", 0) >= warning_ms for c in [nia_result, rest_result] if c.get("response_time_ms")):
            result["level"] = "WARNING"
            result["alert_message"] = "API response time elevated"
        else:
            result["alert_message"] = "All Reveal AI APIs healthy"

        return result

    def load_state(self) -> Dict:
        """Load previous state."""
        state_file = self.config.get("state_file", "/tmp/reveal_api_health_state.json")
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Could not load state file: {e}")
        return {"consecutive_failures": 0}

    def save_state(self, state: Dict):
        """Save current state."""
        state_file = self.config.get("state_file", "/tmp/reveal_api_health_state.json")
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
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

        # Alert on recovery
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

        nia = result.get("nia_api", {})
        rest = result.get("rest_api", {})

        payload = {
            "attachments": [{
                "color": color,
                "title": f"Reveal AI API Health: {result['level']}",
                "text": result["alert_message"],
                "fields": [
                    {"title": "NIA API", "value": f"{nia.get('status', 'Unknown')} ({nia.get('response_time_ms', 'N/A')}ms)", "short": True},
                    {"title": "REST API", "value": f"{rest.get('status', 'Unknown')} ({rest.get('response_time_ms', 'N/A')}ms)", "short": True}
                ],
                "footer": "Reveal AI API Health Monitor",
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
            "dedup_key": "reveal-api-health",
            "payload": {
                "summary": f"Reveal AI: {result['alert_message']}",
                "source": "Reveal AI API Health Monitor",
                "severity": severity,
                "custom_details": {
                    "nia_api": result.get("nia_api", {}),
                    "rest_api": result.get("rest_api", {})
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

        nia = result.get("nia_api", {})
        rest = result.get("rest_api", {})

        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": f"Reveal AI API Health: {result['level']}",
            "sections": [{
                "activityTitle": f"Reveal AI API Health: {result['level']}",
                "facts": [
                    {"name": "Message", "value": result["alert_message"]},
                    {"name": "NIA API", "value": f"{nia.get('status', 'Unknown')} ({nia.get('response_time_ms', 'N/A')}ms)"},
                    {"name": "REST API", "value": f"{rest.get('status', 'Unknown')} ({rest.get('response_time_ms', 'N/A')}ms)"}
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
            "monitor": "reveal_api_health_monitor",
            "platform": "Reveal AI",
            "level": result["level"],
            "alert_message": result["alert_message"],
            "details": result,
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

        self.send_slack(result)
        self.send_pagerduty(result)
        self.send_teams(result)
        self.send_webhook(result)

    def run(self) -> int:
        """Main monitoring run. Returns exit code."""
        logging.info("Starting Reveal AI API Health check...")

        try:
            # Check both APIs
            nia_result = self.check_nia_health()
            rest_result = self.check_rest_api_health()

            # Analyze results
            result = self.analyze_health(nia_result, rest_result)

            # Log results
            logging.info(f"API Health Status: {result['level']}")
            logging.info(f"NIA API: {nia_result['status']} ({nia_result.get('response_time_ms', 'N/A')}ms)")
            logging.info(f"REST API: {rest_result['status']} ({rest_result.get('response_time_ms', 'N/A')}ms)")
            logging.info(f"Message: {result['alert_message']}")

            # Check if should alert
            previous_state = self.load_state()
            if self.should_alert(result, previous_state):
                logging.info(f"Sending {result['level']} alert...")
                self.send_notifications(result)

            # Save state
            self.save_state({
                "level": result["level"],
                "all_healthy": result["all_healthy"],
                "timestamp": result["timestamp"]
            })

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

    # Environment variable overrides
    env_mappings = {
        "REVEAL_HOST": "reveal_host",
        "REVEAL_NIA_HOST": "nia_host",
        "REVEAL_NIA_PORT": "nia_port",
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
    if os.environ.get("PAGERDUTY_ENABLED", "").lower() == "true":
        config.setdefault("notifications", {})["pagerduty_enabled"] = True
    if os.environ.get("PAGERDUTY_ROUTING_KEY"):
        config.setdefault("notifications", {})["pagerduty_routing_key"] = os.environ["PAGERDUTY_ROUTING_KEY"]

    return config


def main():
    parser = argparse.ArgumentParser(
        description="Monitor Reveal AI API Health"
    )
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--dry-run", action="store_true", help="Check only, don't send alerts")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()
    config = load_config(args.config)

    if not config.get("reveal_host") and not config.get("nia_host"):
        print("ERROR: reveal_host or nia_host is required")
        sys.exit(1)

    monitor = RevealAPIHealthMonitor(
        config=config,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    exit_code = monitor.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
