#!/usr/bin/env python3
"""
RelativityOne Billing Agent Monitor

Monitors the Billing Agent - a single-instance agent critical for:
- Usage metering and billing accuracy
- Compliance reporting
- License tracking

If this agent fails, billing data stops being collected which can lead to
compliance issues and inaccurate usage reporting.

Usage:
    python billing_agent_monitor.py --config config.json
    python billing_agent_monitor.py --config config.json --dry-run --verbose
"""

import argparse
import json
import logging
import os
import sys
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
from dateutil import parser as date_parser

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

DEFAULT_CONFIG = {
    "relativity_host": "",
    "client_id": "",
    "client_secret": "",
    "username": "",
    "password": "",
    "auth_method": "bearer",
    "agent_name_contains": "Billing",
    "activity_warning_minutes": 60,
    "activity_high_minutes": 120,
    "activity_critical_minutes": 240,
    "notifications": {
        "email_enabled": False,
        "slack_enabled": False,
        "pagerduty_enabled": False,
        "teams_enabled": False,
        "webhook_enabled": False
    },
    "state_file": "/tmp/billing_agent_state.json"
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


class BillingAgentMonitor:
    """Monitor the RelativityOne Billing Agent."""

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

    def get_agents(self) -> List[Dict]:
        """Query the Agents API to get all agents."""
        url = f"{self.config['relativity_host']}/Relativity.REST/api/relativity-environment/v1/agents"

        headers = {
            **self.auth.get_auth_header(),
            "X-CSRF-Header": "-",
            "Content-Type": "application/json"
        }

        try:
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to query agents: {e}")
            raise

    def find_billing_agent(self, agents: List[Dict]) -> Optional[Dict]:
        """Find the Billing Agent from the list of agents."""
        search_term = self.config.get("agent_name_contains", "Billing").lower()

        for agent in agents:
            agent_name = agent.get("Name", "").lower()
            if search_term in agent_name:
                return agent

        return None

    def check_agent_status(self, agent: Dict) -> Dict[str, Any]:
        """Check the status of the Billing Agent and determine alert level."""
        result = {
            "agent_name": agent.get("Name", "Unknown"),
            "artifact_id": agent.get("ArtifactID"),
            "enabled": agent.get("Enabled", False),
            "status": agent.get("Status", "Unknown"),
            "message": agent.get("Message", ""),
            "last_activity": agent.get("LastActivityDate"),
            "server": agent.get("Server", {}).get("Name", "Unknown"),
            "level": "OK",
            "alert_message": "",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Check if agent is disabled - CRITICAL
        if not result["enabled"]:
            result["level"] = "CRITICAL"
            result["alert_message"] = "BILLING AGENT DISABLED - Usage metering has stopped!"
            return result

        # Check agent status
        status = result["status"].lower() if result["status"] else ""
        if status in ["not responding", "service not responding"]:
            result["level"] = "CRITICAL"
            result["alert_message"] = "BILLING AGENT NOT RESPONDING - Billing data collection halted!"
            return result

        # Check last activity time
        if result["last_activity"]:
            try:
                last_activity = date_parser.parse(result["last_activity"])
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=timezone.utc)

                now = datetime.now(timezone.utc)
                age_minutes = (now - last_activity).total_seconds() / 60
                result["activity_age_minutes"] = round(age_minutes, 1)

                critical_threshold = self.config.get("activity_critical_minutes", 240)
                high_threshold = self.config.get("activity_high_minutes", 120)
                warning_threshold = self.config.get("activity_warning_minutes", 60)

                if age_minutes >= critical_threshold:
                    result["level"] = "CRITICAL"
                    result["alert_message"] = f"Billing Agent last activity was {round(age_minutes)} minutes ago (threshold: {critical_threshold} min)"
                elif age_minutes >= high_threshold:
                    result["level"] = "HIGH"
                    result["alert_message"] = f"Billing Agent last activity was {round(age_minutes)} minutes ago (threshold: {high_threshold} min)"
                elif age_minutes >= warning_threshold:
                    result["level"] = "WARNING"
                    result["alert_message"] = f"Billing Agent last activity was {round(age_minutes)} minutes ago (threshold: {warning_threshold} min)"

            except (ValueError, TypeError) as e:
                logging.warning(f"Could not parse last activity date: {e}")

        if result["level"] == "OK":
            result["alert_message"] = "Billing Agent is healthy and running normally"

        return result

    def load_state(self) -> Dict:
        """Load previous state to prevent duplicate alerts."""
        state_file = self.config.get("state_file", "/tmp/billing_agent_state.json")
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Could not load state file: {e}")
        return {}

    def save_state(self, state: Dict):
        """Save current state for future comparisons."""
        state_file = self.config.get("state_file", "/tmp/billing_agent_state.json")
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except IOError as e:
            logging.warning(f"Could not save state file: {e}")

    def should_alert(self, result: Dict, previous_state: Dict) -> bool:
        """Determine if we should send an alert based on state changes."""
        current_level = result["level"]
        previous_level = previous_state.get("level", "OK")

        # Always alert on CRITICAL
        if current_level == "CRITICAL":
            return True

        # Alert if level increased
        if ALERT_LEVELS.get(current_level, 0) > ALERT_LEVELS.get(previous_level, 0):
            return True

        # Alert if transitioning from problem to OK (recovery)
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
            msg['Subject'] = f"[{result['level']}] RelativityOne Billing Agent Alert"

            body = f"""
RelativityOne Billing Agent Monitor Alert

Level: {result['level']}
Agent: {result['agent_name']}
Status: {result['status']}
Enabled: {result['enabled']}
Server: {result['server']}
Last Activity: {result.get('last_activity', 'Unknown')}
Activity Age: {result.get('activity_age_minutes', 'N/A')} minutes

Message: {result['alert_message']}

Timestamp: {result['timestamp']}

---
This is an automated alert from the RelativityOne Billing Agent Monitor.
See RUNBOOK-006 for response procedures.
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

        payload = {
            "attachments": [{
                "color": color,
                "title": f"Billing Agent Alert: {result['level']}",
                "text": result["alert_message"],
                "fields": [
                    {"title": "Agent", "value": result["agent_name"], "short": True},
                    {"title": "Status", "value": result["status"], "short": True},
                    {"title": "Enabled", "value": str(result["enabled"]), "short": True},
                    {"title": "Server", "value": result["server"], "short": True},
                    {"title": "Last Activity", "value": str(result.get("activity_age_minutes", "N/A")) + " min ago", "short": True}
                ],
                "footer": "RelativityOne Billing Agent Monitor",
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

        # Resolve if OK, otherwise trigger
        event_action = "resolve" if result["level"] == "OK" else "trigger"

        payload = {
            "routing_key": routing_key,
            "event_action": event_action,
            "dedup_key": "relativity-billing-agent",
            "payload": {
                "summary": f"Billing Agent: {result['alert_message']}",
                "source": "RelativityOne Billing Agent Monitor",
                "severity": severity,
                "custom_details": {
                    "agent_name": result["agent_name"],
                    "status": result["status"],
                    "enabled": result["enabled"],
                    "server": result["server"],
                    "last_activity": result.get("last_activity"),
                    "activity_age_minutes": result.get("activity_age_minutes")
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
            "summary": f"Billing Agent Alert: {result['level']}",
            "sections": [{
                "activityTitle": f"Billing Agent Alert: {result['level']}",
                "facts": [
                    {"name": "Agent", "value": result["agent_name"]},
                    {"name": "Status", "value": result["status"]},
                    {"name": "Enabled", "value": str(result["enabled"])},
                    {"name": "Server", "value": result["server"]},
                    {"name": "Last Activity", "value": f"{result.get('activity_age_minutes', 'N/A')} minutes ago"},
                    {"name": "Message", "value": result["alert_message"]}
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
            "monitor": "billing_agent_monitor",
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

        self.send_email(result)
        self.send_slack(result)
        self.send_pagerduty(result)
        self.send_teams(result)
        self.send_webhook(result)

    def run(self) -> int:
        """Main monitoring loop. Returns exit code based on alert level."""
        logging.info("Starting Billing Agent monitoring check...")

        try:
            # Get all agents
            agents = self.get_agents()
            logging.debug(f"Found {len(agents)} total agents")

            # Find the Billing Agent
            billing_agent = self.find_billing_agent(agents)

            if not billing_agent:
                result = {
                    "level": "CRITICAL",
                    "alert_message": "BILLING AGENT NOT FOUND - Agent may be deleted or renamed!",
                    "agent_name": "Not Found",
                    "status": "Unknown",
                    "enabled": False,
                    "server": "Unknown",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                result = self.check_agent_status(billing_agent)

            # Log the result
            logging.info(f"Billing Agent Status: {result['level']}")
            logging.info(f"Agent: {result['agent_name']}")
            logging.info(f"Enabled: {result['enabled']}")
            logging.info(f"Status: {result['status']}")
            if result.get('activity_age_minutes'):
                logging.info(f"Last Activity: {result['activity_age_minutes']} minutes ago")
            logging.info(f"Message: {result['alert_message']}")

            # Check if we should alert
            previous_state = self.load_state()
            if self.should_alert(result, previous_state):
                logging.info(f"Sending {result['level']} alert...")
                self.send_notifications(result)
            else:
                logging.debug("No alert needed (no state change)")

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

    # Load from file if provided
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = json.load(f)
            config.update(file_config)

    # Override with environment variables
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

    # Notification environment variables
    if os.environ.get("EMAIL_ENABLED", "").lower() == "true":
        config.setdefault("notifications", {})["email_enabled"] = True
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
        description="Monitor RelativityOne Billing Agent"
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

    monitor = BillingAgentMonitor(
        config=config,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    exit_code = monitor.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
