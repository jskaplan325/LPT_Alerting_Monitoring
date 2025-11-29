#!/usr/bin/env python3
"""
RelativityOne Telemetry Agent Monitor

CRITICAL: This script monitors the Telemetry Metrics Transmission Agent.
If this agent fails, users will be logged out of RelativityOne.

Schedule this script to run every 1 minute via cron, Windows Task Scheduler,
or your preferred scheduling system.

Requirements:
    pip install requests python-dateutil

Configuration:
    Set environment variables or update the CONFIG section below.

Usage:
    python telemetry_agent_monitor.py
    python telemetry_agent_monitor.py --config /path/to/config.json
"""

import os
import sys
import json
import logging
import argparse
import smtplib
import urllib.parse
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List

try:
    import requests
    from dateutil import parser as date_parser
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Run: pip install requests python-dateutil")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    # RelativityOne Connection
    "relativity_host": os.environ.get("RELATIVITY_HOST", "https://your-instance.relativity.one"),
    "client_id": os.environ.get("RELATIVITY_CLIENT_ID", ""),
    "client_secret": os.environ.get("RELATIVITY_CLIENT_SECRET", ""),

    # Alternative: Basic Auth (less secure, use client credentials if possible)
    "username": os.environ.get("RELATIVITY_USERNAME", ""),
    "password": os.environ.get("RELATIVITY_PASSWORD", ""),
    "auth_method": os.environ.get("RELATIVITY_AUTH_METHOD", "bearer"),  # "bearer" or "basic"

    # Agent to Monitor
    "agent_name_contains": "Telemetry",  # Partial match for agent name

    # Alert Thresholds (in hours)
    "warning_threshold_hours": 6,
    "high_threshold_hours": 12,
    "critical_threshold_hours": 24,

    # Last Activity Thresholds (in minutes)
    "activity_warning_minutes": 30,
    "activity_high_minutes": 60,
    "activity_critical_minutes": 120,

    # Notification Settings
    "notifications": {
        # Email Settings
        "email_enabled": os.environ.get("EMAIL_ENABLED", "false").lower() == "true",
        "smtp_server": os.environ.get("SMTP_SERVER", "smtp.office365.com"),
        "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
        "smtp_username": os.environ.get("SMTP_USERNAME", ""),
        "smtp_password": os.environ.get("SMTP_PASSWORD", ""),
        "email_from": os.environ.get("EMAIL_FROM", "alerts@company.com"),
        "email_to": os.environ.get("EMAIL_TO", "oncall@company.com").split(","),

        # Slack Webhook
        "slack_enabled": os.environ.get("SLACK_ENABLED", "false").lower() == "true",
        "slack_webhook_url": os.environ.get("SLACK_WEBHOOK_URL", ""),

        # PagerDuty
        "pagerduty_enabled": os.environ.get("PAGERDUTY_ENABLED", "false").lower() == "true",
        "pagerduty_routing_key": os.environ.get("PAGERDUTY_ROUTING_KEY", ""),

        # Microsoft Teams Webhook
        "teams_enabled": os.environ.get("TEAMS_ENABLED", "false").lower() == "true",
        "teams_webhook_url": os.environ.get("TEAMS_WEBHOOK_URL", ""),

        # Generic Webhook (for custom integrations)
        "webhook_enabled": os.environ.get("WEBHOOK_ENABLED", "false").lower() == "true",
        "webhook_url": os.environ.get("WEBHOOK_URL", ""),
    },

    # Logging
    "log_file": os.environ.get("LOG_FILE", "/var/log/telemetry_agent_monitor.log"),
    "log_level": os.environ.get("LOG_LEVEL", "INFO"),

    # State file to track alert state (avoid duplicate alerts)
    "state_file": os.environ.get("STATE_FILE", "/tmp/telemetry_agent_state.json"),
}


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging(config: Dict) -> logging.Logger:
    """Configure logging."""
    logger = logging.getLogger("TelemetryAgentMonitor")
    logger.setLevel(getattr(logging, config["log_level"].upper(), logging.INFO))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (if writable)
    try:
        file_handler = logging.FileHandler(config["log_file"])
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    except (PermissionError, FileNotFoundError):
        logger.warning(f"Cannot write to log file: {config['log_file']}")

    return logger


# =============================================================================
# AUTHENTICATION
# =============================================================================

class RelativityAuth:
    """Handle RelativityOne authentication."""

    def __init__(self, config: Dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.token = None
        self.token_expiry = None

    def get_bearer_token(self) -> str:
        """Get OAuth bearer token."""
        token_url = f"{self.config['relativity_host']}/Relativity/Identity/connect/token"

        payload = {
            "grant_type": "client_credentials",
            "scope": "SystemUserInfo",
            "client_id": self.config["client_id"],
            "client_secret": self.config["client_secret"],
        }

        try:
            response = requests.post(
                token_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data["access_token"]
            # Tokens typically expire in 1 hour, refresh at 50 minutes
            self.token_expiry = datetime.now(timezone.utc) + timedelta(minutes=50)
            self.logger.debug("Successfully obtained bearer token")
            return self.token
        except Exception as e:
            self.logger.error(f"Failed to get bearer token: {e}")
            raise

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        headers = {
            "X-CSRF-Header": "-",
            "Content-Type": "application/json",
        }

        if self.config["auth_method"] == "bearer":
            if not self.token or (self.token_expiry and datetime.now(timezone.utc) >= self.token_expiry):
                self.get_bearer_token()
            headers["Authorization"] = f"Bearer {self.token}"
        else:
            # Basic auth
            import base64
            credentials = base64.b64encode(
                f"{self.config['username']}:{self.config['password']}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"

        return headers


# =============================================================================
# AGENT MONITORING
# =============================================================================

class TelemetryAgentMonitor:
    """Monitor the Telemetry Metrics Transmission Agent."""

    def __init__(self, config: Dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.auth = RelativityAuth(config, logger)
        self.state = self.load_state()

    def load_state(self) -> Dict:
        """Load previous state to track alert status."""
        try:
            with open(self.config["state_file"], "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"last_alert_level": None, "last_alert_time": None}

    def save_state(self):
        """Save current state."""
        try:
            with open(self.config["state_file"], "w") as f:
                json.dump(self.state, f)
        except Exception as e:
            self.logger.warning(f"Failed to save state: {e}")

    def get_agents(self) -> List[Dict]:
        """Query all agents from RelativityOne."""
        url = f"{self.config['relativity_host']}/Relativity.REST/api/relativity-environment/v1/agents"

        try:
            response = requests.get(
                url,
                headers=self.auth.get_auth_headers(),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to query agents: {e}")
            raise

    def find_telemetry_agent(self, agents: List[Dict]) -> Optional[Dict]:
        """Find the Telemetry Metrics Transmission Agent."""
        search_term = self.config["agent_name_contains"].lower()

        for agent in agents:
            agent_name = agent.get("Name", "").lower()
            if search_term in agent_name:
                self.logger.debug(f"Found telemetry agent: {agent.get('Name')}")
                return agent

        return None

    def check_agent_status(self, agent: Dict) -> Dict[str, Any]:
        """
        Check the agent status and return assessment.

        Returns dict with:
            - level: "OK", "WARNING", "HIGH", "CRITICAL"
            - enabled: bool
            - status: str
            - last_activity: datetime or None
            - last_activity_age_minutes: int
            - message: str
            - details: str
        """
        result = {
            "level": "OK",
            "enabled": agent.get("Enabled", False),
            "status": agent.get("Status", "Unknown"),
            "last_activity": None,
            "last_activity_age_minutes": None,
            "message": "",
            "details": "",
            "agent_name": agent.get("Name", "Unknown"),
            "agent_id": agent.get("ArtifactID", "Unknown"),
        }

        # Check if enabled
        if not result["enabled"]:
            result["level"] = "CRITICAL"
            result["message"] = "TELEMETRY AGENT DISABLED - Users may be logged out!"
            result["details"] = "The Telemetry Metrics Transmission Agent is DISABLED. Re-enable immediately."
            return result

        # Check status
        status = result["status"].lower()
        if "not responding" in status or "error" in status or "failed" in status:
            result["level"] = "CRITICAL"
            result["message"] = f"TELEMETRY AGENT NOT RESPONDING - Status: {result['status']}"
            result["details"] = "The agent is not responding. Escalate to Relativity Support immediately."
            return result

        # Check last activity
        last_activity_str = agent.get("LastActivityDate") or agent.get("LastActivity")
        if last_activity_str:
            try:
                last_activity = date_parser.parse(last_activity_str)
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=timezone.utc)
                result["last_activity"] = last_activity

                now = datetime.now(timezone.utc)
                age = now - last_activity
                age_minutes = int(age.total_seconds() / 60)
                result["last_activity_age_minutes"] = age_minutes

                # Check against thresholds
                if age_minutes >= self.config["activity_critical_minutes"]:
                    result["level"] = "CRITICAL"
                    result["message"] = f"TELEMETRY AGENT STALE - No activity for {age_minutes} minutes"
                    result["details"] = f"Last activity: {last_activity.isoformat()}. Threshold: {self.config['activity_critical_minutes']} minutes."
                elif age_minutes >= self.config["activity_high_minutes"]:
                    result["level"] = "HIGH"
                    result["message"] = f"Telemetry agent inactive for {age_minutes} minutes"
                    result["details"] = f"Last activity: {last_activity.isoformat()}. Investigate promptly."
                elif age_minutes >= self.config["activity_warning_minutes"]:
                    result["level"] = "WARNING"
                    result["message"] = f"Telemetry agent activity warning - {age_minutes} minutes since last activity"
                    result["details"] = f"Last activity: {last_activity.isoformat()}. Monitor closely."
                else:
                    result["message"] = "Telemetry agent is healthy"
                    result["details"] = f"Last activity: {age_minutes} minutes ago. Status: {result['status']}."

            except Exception as e:
                self.logger.warning(f"Failed to parse last activity date: {e}")
                result["level"] = "WARNING"
                result["message"] = "Unable to determine last activity time"
                result["details"] = f"Could not parse LastActivityDate: {last_activity_str}"
        else:
            result["level"] = "WARNING"
            result["message"] = "No last activity timestamp available"
            result["details"] = "The agent does not have a LastActivityDate. Unable to verify sync status."

        return result

    def run_check(self) -> Dict[str, Any]:
        """Run the telemetry agent check."""
        self.logger.info("Starting telemetry agent check...")

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": False,
            "agent_found": False,
            "check_result": None,
            "error": None,
        }

        try:
            # Get all agents
            agents = self.get_agents()
            self.logger.info(f"Retrieved {len(agents)} agents")

            # Find telemetry agent
            telemetry_agent = self.find_telemetry_agent(agents)

            if not telemetry_agent:
                result["error"] = "CRITICAL: Telemetry agent not found!"
                result["check_result"] = {
                    "level": "CRITICAL",
                    "message": "Telemetry Metrics Transmission Agent NOT FOUND",
                    "details": "Could not find the telemetry agent in the agents list. This may indicate a serious configuration issue.",
                }
                self.logger.critical(result["error"])
            else:
                result["agent_found"] = True
                result["check_result"] = self.check_agent_status(telemetry_agent)
                result["success"] = True

                self.logger.info(
                    f"Check complete - Level: {result['check_result']['level']}, "
                    f"Enabled: {result['check_result']['enabled']}, "
                    f"Status: {result['check_result']['status']}"
                )

        except Exception as e:
            result["error"] = str(e)
            result["check_result"] = {
                "level": "CRITICAL",
                "message": f"Failed to check telemetry agent: {e}",
                "details": "The monitoring script encountered an error. This may indicate authentication or connectivity issues.",
            }
            self.logger.error(f"Check failed: {e}")

        return result


# =============================================================================
# NOTIFICATIONS
# =============================================================================

class NotificationManager:
    """Handle sending alerts via various channels."""

    def __init__(self, config: Dict, logger: logging.Logger):
        self.config = config["notifications"]
        self.logger = logger

    def send_email(self, subject: str, body: str, is_html: bool = False):
        """Send email notification."""
        if not self.config["email_enabled"]:
            return

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.config["email_from"]
            msg["To"] = ", ".join(self.config["email_to"])

            content_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, content_type))

            with smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"]) as server:
                server.starttls()
                if self.config["smtp_username"]:
                    server.login(self.config["smtp_username"], self.config["smtp_password"])
                server.sendmail(
                    self.config["email_from"],
                    self.config["email_to"],
                    msg.as_string()
                )

            self.logger.info("Email notification sent")
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")

    def send_slack(self, message: str, level: str):
        """Send Slack notification."""
        if not self.config["slack_enabled"]:
            return

        try:
            color_map = {
                "CRITICAL": "danger",
                "HIGH": "warning",
                "WARNING": "#ffcc00",
                "OK": "good",
            }

            payload = {
                "attachments": [{
                    "color": color_map.get(level, "#808080"),
                    "title": f"RelativityOne Telemetry Agent Alert - {level}",
                    "text": message,
                    "footer": "Telemetry Agent Monitor",
                    "ts": int(datetime.now().timestamp()),
                }]
            }

            response = requests.post(
                self.config["slack_webhook_url"],
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            self.logger.info("Slack notification sent")
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")

    def send_pagerduty(self, message: str, level: str, details: str):
        """Send PagerDuty alert."""
        if not self.config["pagerduty_enabled"]:
            return

        try:
            severity_map = {
                "CRITICAL": "critical",
                "HIGH": "error",
                "WARNING": "warning",
                "OK": "info",
            }

            payload = {
                "routing_key": self.config["pagerduty_routing_key"],
                "event_action": "trigger" if level in ["CRITICAL", "HIGH"] else "resolve",
                "dedup_key": "relativity-telemetry-agent",
                "payload": {
                    "summary": message,
                    "severity": severity_map.get(level, "info"),
                    "source": "RelativityOne Telemetry Monitor",
                    "custom_details": {
                        "details": details,
                        "level": level,
                    }
                }
            }

            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            self.logger.info("PagerDuty notification sent")
        except Exception as e:
            self.logger.error(f"Failed to send PagerDuty notification: {e}")

    def send_teams(self, message: str, level: str, details: str):
        """Send Microsoft Teams notification."""
        if not self.config["teams_enabled"]:
            return

        try:
            color_map = {
                "CRITICAL": "FF0000",
                "HIGH": "FFA500",
                "WARNING": "FFFF00",
                "OK": "00FF00",
            }

            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": color_map.get(level, "808080"),
                "summary": f"Telemetry Agent Alert - {level}",
                "sections": [{
                    "activityTitle": f"RelativityOne Telemetry Agent - {level}",
                    "facts": [
                        {"name": "Status", "value": level},
                        {"name": "Message", "value": message},
                        {"name": "Details", "value": details},
                    ],
                    "markdown": True
                }]
            }

            response = requests.post(
                self.config["teams_webhook_url"],
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            self.logger.info("Teams notification sent")
        except Exception as e:
            self.logger.error(f"Failed to send Teams notification: {e}")

    def send_webhook(self, check_result: Dict):
        """Send generic webhook notification."""
        if not self.config["webhook_enabled"]:
            return

        try:
            payload = {
                "source": "relativity-telemetry-monitor",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": check_result.get("level"),
                "message": check_result.get("message"),
                "details": check_result.get("details"),
                "agent_enabled": check_result.get("enabled"),
                "agent_status": check_result.get("status"),
                "last_activity_age_minutes": check_result.get("last_activity_age_minutes"),
            }

            response = requests.post(
                self.config["webhook_url"],
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            self.logger.info("Webhook notification sent")
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")

    def send_alert(self, check_result: Dict):
        """Send alerts via all configured channels."""
        level = check_result.get("level", "UNKNOWN")
        message = check_result.get("message", "Unknown issue")
        details = check_result.get("details", "")

        # Only send alerts for WARNING and above
        if level == "OK":
            self.logger.info("Status OK - no alerts sent")
            return

        self.logger.info(f"Sending {level} alerts...")

        # Email
        subject = f"[{level}] RelativityOne Telemetry Agent Alert"
        email_body = f"""
RelativityOne Telemetry Agent Monitor Alert

Level: {level}
Time: {datetime.now(timezone.utc).isoformat()}

Message: {message}

Details: {details}

Agent Status:
- Enabled: {check_result.get('enabled')}
- Status: {check_result.get('status')}
- Last Activity: {check_result.get('last_activity_age_minutes')} minutes ago

ACTION REQUIRED: Review the telemetry agent immediately.
If CRITICAL, users may be at risk of being logged out.

See RUNBOOK-018 for response procedures.
"""
        self.send_email(subject, email_body)

        # Slack
        self.send_slack(f"{message}\n\n{details}", level)

        # PagerDuty
        self.send_pagerduty(message, level, details)

        # Teams
        self.send_teams(message, level, details)

        # Generic webhook
        self.send_webhook(check_result)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Monitor RelativityOne Telemetry Agent")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--dry-run", action="store_true", help="Check only, don't send alerts")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Load config from file if provided
    config = CONFIG.copy()
    if args.config:
        try:
            with open(args.config, "r") as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Failed to load config file: {e}")
            sys.exit(1)

    # Set verbose logging
    if args.verbose:
        config["log_level"] = "DEBUG"

    # Setup logging
    logger = setup_logging(config)
    logger.info("=" * 60)
    logger.info("Telemetry Agent Monitor Starting")
    logger.info("=" * 60)

    # Validate configuration
    if config["auth_method"] == "bearer":
        if not config["client_id"] or not config["client_secret"]:
            logger.error("Client ID and Client Secret required for bearer auth")
            logger.error("Set RELATIVITY_CLIENT_ID and RELATIVITY_CLIENT_SECRET environment variables")
            sys.exit(1)
    else:
        if not config["username"] or not config["password"]:
            logger.error("Username and Password required for basic auth")
            sys.exit(1)

    # Run monitor
    monitor = TelemetryAgentMonitor(config, logger)
    result = monitor.run_check()

    # Output result
    print(json.dumps(result, indent=2, default=str))

    # Send notifications (unless dry run)
    if not args.dry_run and result.get("check_result"):
        notifier = NotificationManager(config, logger)
        notifier.send_alert(result["check_result"])

    # Save state
    if result.get("check_result"):
        monitor.state["last_alert_level"] = result["check_result"].get("level")
        monitor.state["last_alert_time"] = datetime.now(timezone.utc).isoformat()
        monitor.save_state()

    # Exit with appropriate code
    level = result.get("check_result", {}).get("level", "CRITICAL")
    exit_codes = {"OK": 0, "WARNING": 1, "HIGH": 2, "CRITICAL": 3}
    sys.exit(exit_codes.get(level, 3))


if __name__ == "__main__":
    main()
