#!/usr/bin/env python3
"""
RelativityOne Worker Health Monitor

Monitors all worker services across the RelativityOne environment.
Workers are responsible for executing all background jobs including:
- Processing jobs
- Production jobs
- Imaging jobs
- Analytics jobs
- OCR jobs

If workers go down, ALL job processing stops.

Usage:
    python worker_health_monitor.py --config config.json
    python worker_health_monitor.py --config config.json --dry-run --verbose
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
    "min_healthy_workers": 1,
    "unhealthy_worker_threshold_warning": 1,
    "unhealthy_worker_threshold_high": 2,
    "unhealthy_worker_threshold_critical": 3,
    "notifications": {
        "email_enabled": False,
        "slack_enabled": False,
        "pagerduty_enabled": False,
        "teams_enabled": False,
        "webhook_enabled": False
    },
    "state_file": "/tmp/worker_health_state.json"
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


class WorkerHealthMonitor:
    """Monitor RelativityOne Worker Services."""

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

    def get_resource_servers(self) -> List[Dict]:
        """Query the Resource Server API to get worker status."""
        url = f"{self.config['relativity_host']}/Relativity.REST/api/relativity-environment/v1/resource-servers"

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
            logging.error(f"Failed to query resource servers: {e}")
            raise

    def get_agents(self) -> List[Dict]:
        """Query the Agents API to get agent status."""
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

    def analyze_workers(self, resource_servers: List[Dict], agents: List[Dict]) -> Dict[str, Any]:
        """Analyze worker health across the environment."""
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_servers": 0,
            "healthy_servers": 0,
            "unhealthy_servers": 0,
            "server_details": [],
            "total_agents": len(agents),
            "enabled_agents": 0,
            "disabled_agents": 0,
            "not_responding_agents": 0,
            "agent_issues": [],
            "level": "OK",
            "alert_message": ""
        }

        # Analyze resource servers (workers)
        for server in resource_servers:
            result["total_servers"] += 1
            server_info = {
                "name": server.get("Name", "Unknown"),
                "artifact_id": server.get("ArtifactID"),
                "type": server.get("Type", {}).get("Name", "Unknown"),
                "status": server.get("Status", {}).get("Name", "Unknown"),
                "url": server.get("URL", "")
            }

            status = server_info["status"].lower()
            if status in ["active", "online", "running"]:
                result["healthy_servers"] += 1
                server_info["healthy"] = True
            else:
                result["unhealthy_servers"] += 1
                server_info["healthy"] = False

            result["server_details"].append(server_info)

        # Analyze agents
        for agent in agents:
            if agent.get("Enabled", False):
                result["enabled_agents"] += 1
            else:
                result["disabled_agents"] += 1

            status = agent.get("Status", "").lower()
            if status in ["not responding", "service not responding"]:
                result["not_responding_agents"] += 1
                result["agent_issues"].append({
                    "name": agent.get("Name", "Unknown"),
                    "status": agent.get("Status", "Unknown"),
                    "server": agent.get("Server", {}).get("Name", "Unknown"),
                    "message": agent.get("Message", "")
                })

        # Determine alert level
        unhealthy_count = result["unhealthy_servers"] + result["not_responding_agents"]

        critical_threshold = self.config.get("unhealthy_worker_threshold_critical", 3)
        high_threshold = self.config.get("unhealthy_worker_threshold_high", 2)
        warning_threshold = self.config.get("unhealthy_worker_threshold_warning", 1)

        if unhealthy_count >= critical_threshold:
            result["level"] = "CRITICAL"
            result["alert_message"] = f"CRITICAL: {unhealthy_count} workers/agents unhealthy - Job processing severely impacted!"
        elif result["unhealthy_servers"] > 0 and result["healthy_servers"] == 0:
            result["level"] = "CRITICAL"
            result["alert_message"] = "CRITICAL: No healthy worker servers available - ALL job processing stopped!"
        elif unhealthy_count >= high_threshold:
            result["level"] = "HIGH"
            result["alert_message"] = f"HIGH: {unhealthy_count} workers/agents unhealthy - Job processing degraded"
        elif unhealthy_count >= warning_threshold:
            result["level"] = "WARNING"
            result["alert_message"] = f"WARNING: {unhealthy_count} workers/agents unhealthy - Monitor closely"
        else:
            result["alert_message"] = f"All {result['healthy_servers']} worker servers healthy, {result['enabled_agents']} agents enabled"

        return result

    def load_state(self) -> Dict:
        """Load previous state to prevent duplicate alerts."""
        state_file = self.config.get("state_file", "/tmp/worker_health_state.json")
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Could not load state file: {e}")
        return {}

    def save_state(self, state: Dict):
        """Save current state for future comparisons."""
        state_file = self.config.get("state_file", "/tmp/worker_health_state.json")
        try:
            # Save a simplified state for comparison
            simplified = {
                "level": state["level"],
                "unhealthy_servers": state["unhealthy_servers"],
                "not_responding_agents": state["not_responding_agents"],
                "timestamp": state["timestamp"]
            }
            with open(state_file, 'w') as f:
                json.dump(simplified, f, indent=2)
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

        # Alert if number of unhealthy workers changed significantly
        prev_unhealthy = previous_state.get("unhealthy_servers", 0) + previous_state.get("not_responding_agents", 0)
        curr_unhealthy = result["unhealthy_servers"] + result["not_responding_agents"]
        if abs(curr_unhealthy - prev_unhealthy) >= 2:
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
            msg['Subject'] = f"[{result['level']}] RelativityOne Worker Health Alert"

            # Build server status list
            server_status = "\n".join([
                f"  - {s['name']}: {s['status']} ({'Healthy' if s['healthy'] else 'UNHEALTHY'})"
                for s in result.get('server_details', [])
            ])

            # Build agent issues list
            agent_issues = "\n".join([
                f"  - {a['name']}: {a['status']} (Server: {a['server']})"
                for a in result.get('agent_issues', [])
            ]) or "  None"

            body = f"""
RelativityOne Worker Health Alert

Level: {result['level']}
Message: {result['alert_message']}

WORKER SERVER STATUS:
Total Servers: {result['total_servers']}
Healthy: {result['healthy_servers']}
Unhealthy: {result['unhealthy_servers']}

Server Details:
{server_status}

AGENT STATUS:
Total Agents: {result['total_agents']}
Enabled: {result['enabled_agents']}
Disabled: {result['disabled_agents']}
Not Responding: {result['not_responding_agents']}

Agent Issues:
{agent_issues}

Timestamp: {result['timestamp']}

---
This is an automated alert from the RelativityOne Worker Health Monitor.
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

        # Build unhealthy server list for message
        unhealthy_servers = [s['name'] for s in result.get('server_details', []) if not s.get('healthy')]
        unhealthy_text = ", ".join(unhealthy_servers) if unhealthy_servers else "None"

        payload = {
            "attachments": [{
                "color": color,
                "title": f"Worker Health Alert: {result['level']}",
                "text": result["alert_message"],
                "fields": [
                    {"title": "Healthy Servers", "value": str(result["healthy_servers"]), "short": True},
                    {"title": "Unhealthy Servers", "value": str(result["unhealthy_servers"]), "short": True},
                    {"title": "Enabled Agents", "value": str(result["enabled_agents"]), "short": True},
                    {"title": "Not Responding", "value": str(result["not_responding_agents"]), "short": True},
                    {"title": "Unhealthy Workers", "value": unhealthy_text, "short": False}
                ],
                "footer": "RelativityOne Worker Health Monitor",
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
            "dedup_key": "relativity-worker-health",
            "payload": {
                "summary": f"Worker Health: {result['alert_message']}",
                "source": "RelativityOne Worker Health Monitor",
                "severity": severity,
                "custom_details": {
                    "healthy_servers": result["healthy_servers"],
                    "unhealthy_servers": result["unhealthy_servers"],
                    "enabled_agents": result["enabled_agents"],
                    "not_responding_agents": result["not_responding_agents"],
                    "agent_issues": result.get("agent_issues", [])
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
            "summary": f"Worker Health Alert: {result['level']}",
            "sections": [{
                "activityTitle": f"Worker Health Alert: {result['level']}",
                "facts": [
                    {"name": "Message", "value": result["alert_message"]},
                    {"name": "Healthy Servers", "value": str(result["healthy_servers"])},
                    {"name": "Unhealthy Servers", "value": str(result["unhealthy_servers"])},
                    {"name": "Enabled Agents", "value": str(result["enabled_agents"])},
                    {"name": "Not Responding Agents", "value": str(result["not_responding_agents"])}
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
            "monitor": "worker_health_monitor",
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
        logging.info("Starting Worker Health monitoring check...")

        try:
            # Get resource servers and agents
            resource_servers = self.get_resource_servers()
            logging.debug(f"Found {len(resource_servers)} resource servers")

            agents = self.get_agents()
            logging.debug(f"Found {len(agents)} agents")

            # Analyze health
            result = self.analyze_workers(resource_servers, agents)

            # Log the result
            logging.info(f"Worker Health Status: {result['level']}")
            logging.info(f"Servers: {result['healthy_servers']}/{result['total_servers']} healthy")
            logging.info(f"Agents: {result['enabled_agents']} enabled, {result['not_responding_agents']} not responding")
            logging.info(f"Message: {result['alert_message']}")

            # Check if we should alert
            previous_state = self.load_state()
            if self.should_alert(result, previous_state):
                logging.info(f"Sending {result['level']} alert...")
                self.send_notifications(result)
            else:
                logging.debug("No alert needed (no significant state change)")

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
        description="Monitor RelativityOne Worker Health"
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

    monitor = WorkerHealthMonitor(
        config=config,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    exit_code = monitor.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
