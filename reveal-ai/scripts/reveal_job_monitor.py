#!/usr/bin/env python3
"""
Reveal AI Job Monitor

Monitors NIA jobs for failures (Status=4) and stuck jobs (Status=2 for too long).
Uses the 12-state job status model.

Job Status Codes:
    0: Created
    1: Submitted
    2: InProcess (monitor for stuck)
    3: Complete
    4: Error (CRITICAL)
    5: Cancelled (WARNING)
    6: CancelPending
    7: Deleted (AUDIT)
    8: Modified
    9-12: Processing/Deletion states

Usage:
    python reveal_job_monitor.py --config config.json
    python reveal_job_monitor.py --config config.json --dry-run --verbose
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

# Job status codes
JOB_STATUS = {
    0: "Created",
    1: "Submitted",
    2: "InProcess",
    3: "Complete",
    4: "Error",
    5: "Cancelled",
    6: "CancelPending",
    7: "Deleted",
    8: "Modified"
}

DEFAULT_CONFIG = {
    "reveal_host": "",
    "nia_host": "",
    "nia_port": 5566,
    "username": "",
    "password": "",
    "lookback_hours": 24,
    "stuck_job_warning_hours": 4,
    "stuck_job_high_hours": 8,
    "stuck_job_critical_hours": 24,
    "failed_jobs_warning": 1,
    "failed_jobs_high": 3,
    "failed_jobs_critical": 5,
    "monitor_job_types": ["AIDocumentSync", "Index", "Export", "Production", "BulkUpdate", "Deletion"],
    "notifications": {
        "email_enabled": False,
        "slack_enabled": False,
        "pagerduty_enabled": False,
        "teams_enabled": False,
        "webhook_enabled": False
    },
    "state_file": "/tmp/reveal_job_state.json"
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


class RevealJobMonitor:
    """Monitor Reveal AI Jobs via NIA API."""

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

    def get_nia_url(self) -> str:
        """Build NIA API base URL."""
        nia_host = self.config.get("nia_host") or self.config.get("reveal_host", "").replace("https://", "http://")
        nia_port = self.config.get("nia_port", 5566)
        return f"{nia_host}:{nia_port}/nia"

    def get_jobs(self) -> List[Dict]:
        """Query jobs from NIA API."""
        url = f"{self.get_nia_url()}/jobs"

        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to query jobs: {e}")
            # Try alternative endpoint structure
            return self.get_jobs_alternative()

    def get_jobs_alternative(self) -> List[Dict]:
        """Alternative job query method."""
        # Try REST API approach
        try:
            if self.config.get("username") and self.config.get("password"):
                auth = RevealAuth(self.config)
                headers = auth.get_auth_header()

                url = f"{self.config['reveal_host']}/rest/api/v2/jobs"
                response = self.session.get(url, headers=headers, timeout=60)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logging.warning(f"Alternative job query also failed: {e}")

        return []

    def analyze_jobs(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Analyze jobs for failures and stuck states."""
        now = datetime.now(timezone.utc)
        lookback = now - timedelta(hours=self.config.get("lookback_hours", 24))

        result = {
            "timestamp": now.isoformat(),
            "total_jobs": len(jobs),
            "failed_jobs": [],
            "stuck_jobs": [],
            "cancelled_jobs": [],
            "deleted_jobs": [],
            "running_jobs": 0,
            "completed_jobs": 0,
            "level": "OK",
            "alert_message": ""
        }

        stuck_warning = self.config.get("stuck_job_warning_hours", 4)
        stuck_high = self.config.get("stuck_job_high_hours", 8)
        stuck_critical = self.config.get("stuck_job_critical_hours", 24)

        for job in jobs:
            job_id = job.get("jobId") or job.get("id") or job.get("JobId")
            status = job.get("status") or job.get("Status") or job.get("nia_job_status")
            job_type = job.get("jobType") or job.get("type") or job.get("JobType", "Unknown")
            start_time_str = job.get("startTime") or job.get("StartTime") or job.get("created")
            error_details = job.get("errorDetails") or job.get("error") or job.get("message", "")

            # Parse status as integer if string
            if isinstance(status, str):
                status = int(status) if status.isdigit() else -1

            # Parse start time
            start_time = None
            if start_time_str:
                try:
                    start_time = date_parser.parse(start_time_str)
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            # Skip jobs older than lookback (unless still running)
            if start_time and start_time < lookback and status not in [2, 9, 10, 11, 12]:
                continue

            job_info = {
                "job_id": job_id,
                "job_type": job_type,
                "status": status,
                "status_name": JOB_STATUS.get(status, f"Unknown ({status})"),
                "start_time": start_time_str,
                "error": error_details[:200] if error_details else ""
            }

            # Check for failed jobs (Status = 4)
            if status == 4:
                result["failed_jobs"].append(job_info)

            # Check for cancelled jobs (Status = 5)
            elif status == 5:
                result["cancelled_jobs"].append(job_info)

            # Check for deleted jobs (Status = 7)
            elif status == 7:
                result["deleted_jobs"].append(job_info)

            # Check for stuck jobs (Status = 2 or 9-12 for too long)
            elif status in [2, 9, 10, 11, 12]:
                result["running_jobs"] += 1

                if start_time:
                    hours_running = (now - start_time).total_seconds() / 3600
                    if hours_running >= stuck_warning:
                        stuck_level = "WARNING"
                        if hours_running >= stuck_critical:
                            stuck_level = "CRITICAL"
                        elif hours_running >= stuck_high:
                            stuck_level = "HIGH"

                        job_info["hours_running"] = round(hours_running, 1)
                        job_info["stuck_level"] = stuck_level
                        result["stuck_jobs"].append(job_info)

            # Count completed
            elif status == 3:
                result["completed_jobs"] += 1

        # Determine alert level
        self._determine_alert_level(result)

        return result

    def _determine_alert_level(self, result: Dict):
        """Determine overall alert level from analysis."""
        alerts = []
        max_level = "OK"

        failed_count = len(result["failed_jobs"])
        failed_critical = self.config.get("failed_jobs_critical", 5)
        failed_high = self.config.get("failed_jobs_high", 3)
        failed_warning = self.config.get("failed_jobs_warning", 1)

        # Check failed jobs
        if failed_count >= failed_critical:
            max_level = "CRITICAL"
            alerts.append(f"{failed_count} failed jobs (Status=4)")
        elif failed_count >= failed_high:
            max_level = "HIGH"
            alerts.append(f"{failed_count} failed jobs")
        elif failed_count >= failed_warning:
            max_level = "WARNING"
            alerts.append(f"{failed_count} failed jobs")

        # Check stuck jobs
        critical_stuck = [j for j in result["stuck_jobs"] if j.get("stuck_level") == "CRITICAL"]
        high_stuck = [j for j in result["stuck_jobs"] if j.get("stuck_level") == "HIGH"]

        if critical_stuck:
            max_level = "CRITICAL"
            alerts.append(f"{len(critical_stuck)} jobs stuck >24h")
        elif high_stuck:
            if max_level != "CRITICAL":
                max_level = "HIGH"
            alerts.append(f"{len(high_stuck)} jobs stuck >8h")
        elif result["stuck_jobs"]:
            if max_level == "OK":
                max_level = "WARNING"
            alerts.append(f"{len(result['stuck_jobs'])} stuck jobs")

        # Check deleted jobs (audit concern)
        if result["deleted_jobs"]:
            if max_level == "OK":
                max_level = "HIGH"
            alerts.append(f"{len(result['deleted_jobs'])} deletion jobs")

        result["level"] = max_level
        if alerts:
            result["alert_message"] = "; ".join(alerts)
        else:
            result["alert_message"] = f"All jobs healthy - {result['completed_jobs']} completed, {result['running_jobs']} running"

    def load_state(self) -> Dict:
        """Load previous state."""
        state_file = self.config.get("state_file", "/tmp/reveal_job_state.json")
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Could not load state file: {e}")
        return {}

    def save_state(self, state: Dict):
        """Save current state."""
        state_file = self.config.get("state_file", "/tmp/reveal_job_state.json")
        try:
            simplified = {
                "level": state["level"],
                "failed_count": len(state["failed_jobs"]),
                "stuck_count": len(state["stuck_jobs"]),
                "failed_job_ids": [j["job_id"] for j in state["failed_jobs"]],
                "timestamp": state["timestamp"]
            }
            with open(state_file, 'w') as f:
                json.dump(simplified, f, indent=2)
        except IOError as e:
            logging.warning(f"Could not save state file: {e}")

    def should_alert(self, result: Dict, previous_state: Dict) -> bool:
        """Determine if should send alert."""
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

        # Alert on new failed jobs
        prev_failed = set(previous_state.get("failed_job_ids", []))
        curr_failed = set(j["job_id"] for j in result["failed_jobs"])
        if curr_failed - prev_failed:
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

        # Build failed jobs summary
        failed_summary = ", ".join([f"{j['job_type']}({j['job_id']})" for j in result.get('failed_jobs', [])[:5]])
        if len(result.get('failed_jobs', [])) > 5:
            failed_summary += f" (+{len(result['failed_jobs']) - 5} more)"

        payload = {
            "attachments": [{
                "color": color,
                "title": f"Reveal AI Job Monitor: {result['level']}",
                "text": result["alert_message"],
                "fields": [
                    {"title": "Failed Jobs", "value": str(len(result.get("failed_jobs", []))), "short": True},
                    {"title": "Stuck Jobs", "value": str(len(result.get("stuck_jobs", []))), "short": True},
                    {"title": "Running", "value": str(result.get("running_jobs", 0)), "short": True},
                    {"title": "Completed", "value": str(result.get("completed_jobs", 0)), "short": True}
                ],
                "footer": "Reveal AI Job Monitor",
                "ts": int(datetime.now().timestamp())
            }]
        }

        if failed_summary:
            payload["attachments"][0]["fields"].append({
                "title": "Failed",
                "value": failed_summary,
                "short": False
            })

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
            "dedup_key": "reveal-job-monitor",
            "payload": {
                "summary": f"Reveal AI Jobs: {result['alert_message']}",
                "source": "Reveal AI Job Monitor",
                "severity": severity,
                "custom_details": {
                    "failed_jobs": len(result.get("failed_jobs", [])),
                    "stuck_jobs": len(result.get("stuck_jobs", [])),
                    "running_jobs": result.get("running_jobs", 0)
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
            "summary": f"Reveal AI Job Monitor: {result['level']}",
            "sections": [{
                "activityTitle": f"Reveal AI Job Monitor: {result['level']}",
                "facts": [
                    {"name": "Message", "value": result["alert_message"]},
                    {"name": "Failed Jobs", "value": str(len(result.get("failed_jobs", [])))},
                    {"name": "Stuck Jobs", "value": str(len(result.get("stuck_jobs", [])))},
                    {"name": "Running", "value": str(result.get("running_jobs", 0))}
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
        """Send generic webhook."""
        notifications = self.config.get("notifications", {})
        if not notifications.get("webhook_enabled"):
            return

        webhook_url = notifications.get("webhook_url", "")
        if not webhook_url:
            return

        payload = {
            "monitor": "reveal_job_monitor",
            "platform": "Reveal AI",
            "level": result["level"],
            "alert_message": result["alert_message"],
            "failed_jobs": result.get("failed_jobs", []),
            "stuck_jobs": result.get("stuck_jobs", []),
            "timestamp": result["timestamp"]
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logging.info("Webhook notification sent")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send webhook: {e}")

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
        """Main monitoring run."""
        logging.info("Starting Reveal AI Job Monitor check...")

        try:
            # Get jobs
            jobs = self.get_jobs()
            logging.info(f"Retrieved {len(jobs)} jobs")

            # Analyze
            result = self.analyze_jobs(jobs)

            # Log
            logging.info(f"Job Status: {result['level']}")
            logging.info(f"Failed: {len(result['failed_jobs'])}, Stuck: {len(result['stuck_jobs'])}")
            logging.info(f"Running: {result['running_jobs']}, Completed: {result['completed_jobs']}")
            logging.info(f"Message: {result['alert_message']}")

            # Alert if needed
            previous_state = self.load_state()
            if self.should_alert(result, previous_state):
                logging.info(f"Sending {result['level']} alert...")
                self.send_notifications(result)

            # Save state
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
    parser = argparse.ArgumentParser(description="Monitor Reveal AI Jobs")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--dry-run", action="store_true", help="Check only, don't send alerts")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()
    config = load_config(args.config)

    if not config.get("reveal_host") and not config.get("nia_host"):
        print("ERROR: reveal_host or nia_host is required")
        sys.exit(1)

    monitor = RevealJobMonitor(
        config=config,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    exit_code = monitor.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
