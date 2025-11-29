#!/usr/bin/env python3
"""
RelativityOne Job Queue Monitor

Monitors Processing, Production, and Imaging job queues for:
- Failed jobs
- Stuck jobs (running too long)
- Error states
- Queue backlogs

Proactively detects job failures before users notice.

Usage:
    python job_queue_monitor.py --config config.json
    python job_queue_monitor.py --config config.json --dry-run --verbose
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

# Job status mappings
PROCESSING_ERROR_STATES = ["error", "errored", "failed", "cancelled with errors"]
PROCESSING_STUCK_STATES = ["processing", "waiting"]
PRODUCTION_ERROR_STATES = ["error", "errored", "error - job failed"]
IMAGING_ERROR_STATES = ["error", "errored", "failed"]

DEFAULT_CONFIG = {
    "relativity_host": "",
    "client_id": "",
    "client_secret": "",
    "username": "",
    "password": "",
    "auth_method": "bearer",
    "check_processing": True,
    "check_production": True,
    "check_imaging": True,
    "failed_jobs_warning": 1,
    "failed_jobs_high": 3,
    "failed_jobs_critical": 5,
    "stuck_job_hours_warning": 4,
    "stuck_job_hours_high": 8,
    "stuck_job_hours_critical": 24,
    "lookback_hours": 24,
    "notifications": {
        "email_enabled": False,
        "slack_enabled": False,
        "pagerduty_enabled": False,
        "teams_enabled": False,
        "webhook_enabled": False
    },
    "state_file": "/tmp/job_queue_state.json"
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


class JobQueueMonitor:
    """Monitor RelativityOne Job Queues."""

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

    def query_processing_jobs(self) -> List[Dict]:
        """Query processing jobs using Object Manager."""
        url = f"{self.config['relativity_host']}/Relativity.REST/api/Relativity.Objects/workspace/-1/object/query"

        lookback = datetime.now(timezone.utc) - timedelta(hours=self.config.get("lookback_hours", 24))

        payload = {
            "request": {
                "objectType": {"ArtifactTypeID": 1000017},  # Processing Set
                "fields": [
                    {"Name": "Name"},
                    {"Name": "Status"},
                    {"Name": "Workspace"},
                    {"Name": "System Created On"},
                    {"Name": "System Last Modified On"}
                ],
                "condition": "",
                "sorts": [{"FieldIdentifier": {"Name": "System Last Modified On"}, "Direction": "Descending"}],
                "queryHint": ""
            },
            "start": 0,
            "length": 100
        }

        try:
            response = self.session.post(url, headers=self.get_headers(), json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("Objects", [])
        except requests.exceptions.RequestException as e:
            logging.warning(f"Failed to query processing jobs: {e}")
            return []

    def query_production_jobs(self) -> List[Dict]:
        """Query production jobs."""
        url = f"{self.config['relativity_host']}/Relativity.REST/api/Relativity.Objects/workspace/-1/object/query"

        payload = {
            "request": {
                "objectType": {"ArtifactTypeID": 1000023},  # Production Set
                "fields": [
                    {"Name": "Name"},
                    {"Name": "Status"},
                    {"Name": "Workspace"},
                    {"Name": "System Created On"},
                    {"Name": "System Last Modified On"}
                ],
                "condition": "",
                "sorts": [{"FieldIdentifier": {"Name": "System Last Modified On"}, "Direction": "Descending"}],
                "queryHint": ""
            },
            "start": 0,
            "length": 100
        }

        try:
            response = self.session.post(url, headers=self.get_headers(), json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("Objects", [])
        except requests.exceptions.RequestException as e:
            logging.warning(f"Failed to query production jobs: {e}")
            return []

    def query_imaging_jobs(self) -> List[Dict]:
        """Query imaging jobs."""
        url = f"{self.config['relativity_host']}/Relativity.REST/api/Relativity.Objects/workspace/-1/object/query"

        payload = {
            "request": {
                "objectType": {"ArtifactTypeID": 1000020},  # Imaging Set
                "fields": [
                    {"Name": "Name"},
                    {"Name": "Status"},
                    {"Name": "Workspace"},
                    {"Name": "System Created On"},
                    {"Name": "System Last Modified On"}
                ],
                "condition": "",
                "sorts": [{"FieldIdentifier": {"Name": "System Last Modified On"}, "Direction": "Descending"}],
                "queryHint": ""
            },
            "start": 0,
            "length": 100
        }

        try:
            response = self.session.post(url, headers=self.get_headers(), json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("Objects", [])
        except requests.exceptions.RequestException as e:
            logging.warning(f"Failed to query imaging jobs: {e}")
            return []

    def extract_field_value(self, obj: Dict, field_name: str) -> Any:
        """Extract field value from Object Manager response."""
        for field in obj.get("FieldValues", []):
            if field.get("Field", {}).get("Name") == field_name:
                value = field.get("Value")
                # Handle choice fields
                if isinstance(value, dict) and "Name" in value:
                    return value["Name"]
                # Handle workspace/object references
                if isinstance(value, dict) and "ArtifactID" in value:
                    return value.get("Name", str(value["ArtifactID"]))
                return value
        return None

    def analyze_jobs(self, jobs: List[Dict], job_type: str, error_states: List[str]) -> Dict[str, Any]:
        """Analyze jobs for failures and stuck states."""
        analysis = {
            "job_type": job_type,
            "total_jobs": len(jobs),
            "failed_jobs": [],
            "stuck_jobs": [],
            "running_jobs": 0,
            "completed_jobs": 0
        }

        now = datetime.now(timezone.utc)
        lookback = now - timedelta(hours=self.config.get("lookback_hours", 24))

        stuck_warning = self.config.get("stuck_job_hours_warning", 4)
        stuck_high = self.config.get("stuck_job_hours_high", 8)
        stuck_critical = self.config.get("stuck_job_hours_critical", 24)

        for job in jobs:
            name = self.extract_field_value(job, "Name") or "Unknown"
            status = (self.extract_field_value(job, "Status") or "").lower()
            workspace = self.extract_field_value(job, "Workspace") or "Unknown"
            modified = self.extract_field_value(job, "System Last Modified On")

            # Parse modification time
            mod_time = None
            if modified:
                try:
                    mod_time = date_parser.parse(modified)
                    if mod_time.tzinfo is None:
                        mod_time = mod_time.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            # Skip jobs older than lookback period
            if mod_time and mod_time < lookback:
                continue

            # Check for failed jobs
            if any(err in status for err in error_states):
                analysis["failed_jobs"].append({
                    "name": name,
                    "status": status,
                    "workspace": workspace,
                    "artifact_id": job.get("ArtifactID"),
                    "modified": modified
                })

            # Check for stuck jobs (in progress for too long)
            elif any(s in status for s in ["processing", "running", "in progress", "staging"]):
                analysis["running_jobs"] += 1

                if mod_time:
                    hours_running = (now - mod_time).total_seconds() / 3600
                    if hours_running >= stuck_warning:
                        stuck_level = "WARNING"
                        if hours_running >= stuck_critical:
                            stuck_level = "CRITICAL"
                        elif hours_running >= stuck_high:
                            stuck_level = "HIGH"

                        analysis["stuck_jobs"].append({
                            "name": name,
                            "status": status,
                            "workspace": workspace,
                            "artifact_id": job.get("ArtifactID"),
                            "hours_running": round(hours_running, 1),
                            "level": stuck_level
                        })

            elif "completed" in status or "finished" in status:
                analysis["completed_jobs"] += 1

        return analysis

    def determine_alert_level(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Determine overall alert level from job analyses."""
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "OK",
            "alert_message": "",
            "total_failed": 0,
            "total_stuck": 0,
            "analyses": analyses,
            "failed_jobs": [],
            "stuck_jobs": []
        }

        # Aggregate failures and stuck jobs
        for analysis in analyses:
            result["total_failed"] += len(analysis["failed_jobs"])
            result["total_stuck"] += len(analysis["stuck_jobs"])
            result["failed_jobs"].extend(analysis["failed_jobs"])
            result["stuck_jobs"].extend(analysis["stuck_jobs"])

        # Check thresholds
        failed_critical = self.config.get("failed_jobs_critical", 5)
        failed_high = self.config.get("failed_jobs_high", 3)
        failed_warning = self.config.get("failed_jobs_warning", 1)

        # Check for critical stuck jobs
        critical_stuck = [j for j in result["stuck_jobs"] if j.get("level") == "CRITICAL"]
        high_stuck = [j for j in result["stuck_jobs"] if j.get("level") == "HIGH"]

        if result["total_failed"] >= failed_critical or len(critical_stuck) > 0:
            result["level"] = "CRITICAL"
            msgs = []
            if result["total_failed"] >= failed_critical:
                msgs.append(f"{result['total_failed']} failed jobs")
            if critical_stuck:
                msgs.append(f"{len(critical_stuck)} jobs stuck >24h")
            result["alert_message"] = f"CRITICAL: {', '.join(msgs)} - Immediate attention required!"

        elif result["total_failed"] >= failed_high or len(high_stuck) > 0:
            result["level"] = "HIGH"
            msgs = []
            if result["total_failed"] >= failed_high:
                msgs.append(f"{result['total_failed']} failed jobs")
            if high_stuck:
                msgs.append(f"{len(high_stuck)} jobs stuck >8h")
            result["alert_message"] = f"HIGH: {', '.join(msgs)} - Investigation needed"

        elif result["total_failed"] >= failed_warning or result["total_stuck"] > 0:
            result["level"] = "WARNING"
            msgs = []
            if result["total_failed"] >= failed_warning:
                msgs.append(f"{result['total_failed']} failed jobs")
            if result["total_stuck"] > 0:
                msgs.append(f"{result['total_stuck']} stuck jobs")
            result["alert_message"] = f"WARNING: {', '.join(msgs)} - Monitor closely"

        else:
            result["alert_message"] = "All job queues healthy - no failures or stuck jobs detected"

        return result

    def load_state(self) -> Dict:
        """Load previous state to prevent duplicate alerts."""
        state_file = self.config.get("state_file", "/tmp/job_queue_state.json")
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Could not load state file: {e}")
        return {}

    def save_state(self, state: Dict):
        """Save current state for future comparisons."""
        state_file = self.config.get("state_file", "/tmp/job_queue_state.json")
        try:
            simplified = {
                "level": state["level"],
                "total_failed": state["total_failed"],
                "total_stuck": state["total_stuck"],
                "failed_job_ids": [j.get("artifact_id") for j in state["failed_jobs"]],
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

        # Alert if new failed jobs appeared
        prev_failed_ids = set(previous_state.get("failed_job_ids", []))
        curr_failed_ids = set(j.get("artifact_id") for j in result["failed_jobs"])
        if curr_failed_ids - prev_failed_ids:
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
            msg['Subject'] = f"[{result['level']}] RelativityOne Job Queue Alert"

            # Build failed jobs list
            failed_list = "\n".join([
                f"  - {j['name']} ({j['job_type'] if 'job_type' in j else 'Job'}): {j['status']} [Workspace: {j['workspace']}]"
                for j in result.get('failed_jobs', [])
            ]) or "  None"

            # Build stuck jobs list
            stuck_list = "\n".join([
                f"  - {j['name']}: Running for {j['hours_running']}h [{j['level']}] [Workspace: {j['workspace']}]"
                for j in result.get('stuck_jobs', [])
            ]) or "  None"

            body = f"""
RelativityOne Job Queue Monitor Alert

Level: {result['level']}
Message: {result['alert_message']}

FAILED JOBS ({result['total_failed']}):
{failed_list}

STUCK JOBS ({result['total_stuck']}):
{stuck_list}

Timestamp: {result['timestamp']}

---
This is an automated alert from the RelativityOne Job Queue Monitor.
See RUNBOOK-001 (Processing), RUNBOOK-002 (Production), RUNBOOK-003 (Imaging) for response procedures.
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

        # Build failed jobs summary
        failed_summary = ", ".join([f"{j['name']}" for j in result.get('failed_jobs', [])[:5]])
        if len(result.get('failed_jobs', [])) > 5:
            failed_summary += f" (+{len(result['failed_jobs']) - 5} more)"

        payload = {
            "attachments": [{
                "color": color,
                "title": f"Job Queue Alert: {result['level']}",
                "text": result["alert_message"],
                "fields": [
                    {"title": "Failed Jobs", "value": str(result["total_failed"]), "short": True},
                    {"title": "Stuck Jobs", "value": str(result["total_stuck"]), "short": True},
                    {"title": "Failed", "value": failed_summary or "None", "short": False}
                ],
                "footer": "RelativityOne Job Queue Monitor",
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
            "dedup_key": "relativity-job-queue",
            "payload": {
                "summary": f"Job Queue: {result['alert_message']}",
                "source": "RelativityOne Job Queue Monitor",
                "severity": severity,
                "custom_details": {
                    "total_failed": result["total_failed"],
                    "total_stuck": result["total_stuck"],
                    "failed_jobs": result.get("failed_jobs", [])[:10],
                    "stuck_jobs": result.get("stuck_jobs", [])[:10]
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
            "summary": f"Job Queue Alert: {result['level']}",
            "sections": [{
                "activityTitle": f"Job Queue Alert: {result['level']}",
                "facts": [
                    {"name": "Message", "value": result["alert_message"]},
                    {"name": "Failed Jobs", "value": str(result["total_failed"])},
                    {"name": "Stuck Jobs", "value": str(result["total_stuck"])}
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
            "monitor": "job_queue_monitor",
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
        logging.info("Starting Job Queue monitoring check...")

        try:
            analyses = []

            # Check processing jobs
            if self.config.get("check_processing", True):
                logging.debug("Checking processing jobs...")
                processing_jobs = self.query_processing_jobs()
                analysis = self.analyze_jobs(processing_jobs, "Processing", PROCESSING_ERROR_STATES)
                for job in analysis["failed_jobs"]:
                    job["job_type"] = "Processing"
                analyses.append(analysis)
                logging.info(f"Processing: {len(analysis['failed_jobs'])} failed, {len(analysis['stuck_jobs'])} stuck")

            # Check production jobs
            if self.config.get("check_production", True):
                logging.debug("Checking production jobs...")
                production_jobs = self.query_production_jobs()
                analysis = self.analyze_jobs(production_jobs, "Production", PRODUCTION_ERROR_STATES)
                for job in analysis["failed_jobs"]:
                    job["job_type"] = "Production"
                analyses.append(analysis)
                logging.info(f"Production: {len(analysis['failed_jobs'])} failed, {len(analysis['stuck_jobs'])} stuck")

            # Check imaging jobs
            if self.config.get("check_imaging", True):
                logging.debug("Checking imaging jobs...")
                imaging_jobs = self.query_imaging_jobs()
                analysis = self.analyze_jobs(imaging_jobs, "Imaging", IMAGING_ERROR_STATES)
                for job in analysis["failed_jobs"]:
                    job["job_type"] = "Imaging"
                analyses.append(analysis)
                logging.info(f"Imaging: {len(analysis['failed_jobs'])} failed, {len(analysis['stuck_jobs'])} stuck")

            # Determine overall alert level
            result = self.determine_alert_level(analyses)

            # Log the result
            logging.info(f"Job Queue Status: {result['level']}")
            logging.info(f"Total Failed: {result['total_failed']}, Total Stuck: {result['total_stuck']}")
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
        description="Monitor RelativityOne Job Queues"
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

    monitor = JobQueueMonitor(
        config=config,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    exit_code = monitor.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
