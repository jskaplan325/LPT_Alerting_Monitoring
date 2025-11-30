#!/usr/bin/env python3
"""
Relativity aiR Job Monitor

Monitors aiR for Review and aiR for Privilege jobs for:
- Failed jobs (Errored status)
- High document error rates
- Stuck jobs (running too long)
- Pipeline failures (aiR for Privilege)

Proactively detects AI analysis failures before users notice.

Usage:
    python air_job_monitor.py --config config.json
    python air_job_monitor.py --config config.json --dry-run --verbose
    python air_job_monitor.py --config config.json --review-only
    python air_job_monitor.py --config config.json --privilege-only
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

# Import SCOM integration (optional)
try:
    from scom_integration import SCOMIntegration
    SCOM_AVAILABLE = True
except ImportError:
    SCOM_AVAILABLE = False


# Alert levels with exit codes
ALERT_LEVELS = {
    "OK": 0,
    "WARNING": 1,
    "HIGH": 2,
    "CRITICAL": 3
}

# aiR for Review job statuses
AIR_REVIEW_ERROR_STATES = ["errored", "error"]
AIR_REVIEW_RUNNING_STATES = ["in progress", "queued"]

# aiR for Privilege pipeline statuses
AIR_PRIVILEGE_ERROR_STATES = ["run failed", "apply annotations failed"]
AIR_PRIVILEGE_BLOCKED_STATES = ["blocked"]

DEFAULT_CONFIG = {
    "relativity_host": "",
    "client_id": "",
    "client_secret": "",
    "username": "",
    "password": "",
    "auth_method": "bearer",
    "check_air_review": True,
    "check_air_privilege": True,
    "review_error_rate_warning": 0.05,
    "review_error_rate_high": 0.10,
    "review_error_rate_critical": 0.20,
    "review_stuck_multiplier_warning": 2.0,
    "review_stuck_multiplier_high": 4.0,
    "review_stuck_multiplier_critical": 8.0,
    "review_queue_hours_warning": 2,
    "privilege_stale_annotation_hours_warning": 24,
    "privilege_stale_annotation_hours_high": 48,
    "lookback_hours": 48,
    "workspace_ids": [],  # Empty = all workspaces (instance-level)
    "notifications": {
        "email_enabled": False,
        "slack_enabled": False,
        "pagerduty_enabled": False,
        "teams_enabled": False,
        "webhook_enabled": False
    },
    "state_file": "/tmp/air_job_state.json",
    "scom_enabled": False,
    "scom_fallback_file": "/var/log/scom_events.json"
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


class AirJobMonitor:
    """Monitor Relativity aiR Jobs."""

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

        # Initialize SCOM integration
        self.scom = None
        if SCOM_AVAILABLE and self.config.get("scom_enabled", False):
            self.scom = SCOMIntegration(self.config, logging.getLogger(), "air_job", "relativity")
            logging.info("SCOM integration enabled")

    def get_headers(self) -> Dict[str, str]:
        """Get standard headers for API requests."""
        return {
            **self.auth.get_auth_header(),
            "X-CSRF-Header": "-",
            "Content-Type": "application/json"
        }

    def query_air_review_jobs(self) -> List[Dict]:
        """Query aiR for Review jobs using Object Manager."""
        # Use workspace -1 for instance-level query
        url = f"{self.config['relativity_host']}/Relativity.REST/api/Relativity.Objects/workspace/-1/object/query"

        payload = {
            "request": {
                "objectType": {"Name": "aiR for Review Job"},
                "fields": [
                    {"Name": "Name"},
                    {"Name": "Job Status"},
                    {"Name": "Doc Count"},
                    {"Name": "Docs Successful"},
                    {"Name": "Docs Errored"},
                    {"Name": "Docs Skipped"},
                    {"Name": "Docs Pending"},
                    {"Name": "Submitted Time"},
                    {"Name": "Completed Time"},
                    {"Name": "Estimated Run Time"},
                    {"Name": "Estimated Wait Time"},
                    {"Name": "Job Failure Reason"},
                    {"Name": "Workspace"},
                    {"Name": "Prompt Criteria Name"},
                    {"Name": "Project Name"}
                ],
                "condition": "",
                "sorts": [{"FieldIdentifier": {"Name": "Submitted Time"}, "Direction": "Descending"}],
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
            logging.warning(f"Failed to query aiR for Review jobs: {e}")
            return []

    def query_air_privilege_projects(self, workspace_id: int) -> List[Dict]:
        """Query aiR for Privilege projects in a specific workspace."""
        url = f"{self.config['relativity_host']}/Relativity.REST/api/Relativity.Objects/workspace/{workspace_id}/object/query"

        payload = {
            "request": {
                "objectType": {"Name": "aiR for Privilege Project"},
                "fields": [
                    {"Name": "Name"},
                    {"Name": "Status"},
                    {"Name": "Document Count"},
                    {"Name": "System Created On"},
                    {"Name": "System Last Modified On"}
                ],
                "condition": "",
                "sorts": [{"FieldIdentifier": {"Name": "System Last Modified On"}, "Direction": "Descending"}],
                "queryHint": ""
            },
            "start": 0,
            "length": 50
        }

        try:
            response = self.session.post(url, headers=self.get_headers(), json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("Objects", [])
        except requests.exceptions.RequestException as e:
            logging.debug(f"Failed to query aiR for Privilege projects in workspace {workspace_id}: {e}")
            return []

    def get_workspaces(self) -> List[Dict]:
        """Get list of workspaces to check."""
        configured_ids = self.config.get("workspace_ids", [])
        if configured_ids:
            return [{"ArtifactID": wid} for wid in configured_ids]

        # Query all workspaces
        url = f"{self.config['relativity_host']}/Relativity.REST/api/Relativity.Objects/workspace/-1/object/query"

        payload = {
            "request": {
                "objectType": {"ArtifactTypeID": 8},  # Workspace
                "fields": [
                    {"Name": "Name"},
                    {"Name": "ArtifactID"}
                ],
                "condition": "",
                "sorts": [{"FieldIdentifier": {"Name": "Name"}, "Direction": "Ascending"}]
            },
            "start": 0,
            "length": 500
        }

        try:
            response = self.session.post(url, headers=self.get_headers(), json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("Objects", [])
        except requests.exceptions.RequestException as e:
            logging.warning(f"Failed to query workspaces: {e}")
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

    def analyze_air_review_jobs(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Analyze aiR for Review jobs for failures and issues."""
        analysis = {
            "job_type": "aiR for Review",
            "total_jobs": len(jobs),
            "failed_jobs": [],
            "high_error_rate_jobs": [],
            "stuck_jobs": [],
            "long_queue_jobs": [],
            "running_jobs": 0,
            "completed_jobs": 0
        }

        now = datetime.now(timezone.utc)
        lookback = now - timedelta(hours=self.config.get("lookback_hours", 48))

        error_rate_warning = self.config.get("review_error_rate_warning", 0.05)
        error_rate_high = self.config.get("review_error_rate_high", 0.10)
        stuck_warning = self.config.get("review_stuck_multiplier_warning", 2.0)
        stuck_high = self.config.get("review_stuck_multiplier_high", 4.0)
        queue_warning_hours = self.config.get("review_queue_hours_warning", 2)

        for job in jobs:
            name = self.extract_field_value(job, "Name") or self.extract_field_value(job, "Project Name") or "Unknown"
            status = (self.extract_field_value(job, "Job Status") or "").lower()
            workspace = self.extract_field_value(job, "Workspace") or "Unknown"
            submitted = self.extract_field_value(job, "Submitted Time")
            failure_reason = self.extract_field_value(job, "Job Failure Reason")

            doc_count = self.extract_field_value(job, "Doc Count") or 0
            docs_errored = self.extract_field_value(job, "Docs Errored") or 0
            docs_successful = self.extract_field_value(job, "Docs Successful") or 0
            docs_pending = self.extract_field_value(job, "Docs Pending") or 0

            estimated_run = self.extract_field_value(job, "Estimated Run Time")
            estimated_wait = self.extract_field_value(job, "Estimated Wait Time")

            # Parse submitted time
            submit_time = None
            if submitted:
                try:
                    submit_time = date_parser.parse(submitted)
                    if submit_time.tzinfo is None:
                        submit_time = submit_time.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            # Skip jobs older than lookback period
            if submit_time and submit_time < lookback:
                continue

            job_info = {
                "name": name,
                "status": status,
                "workspace": workspace,
                "artifact_id": job.get("ArtifactID"),
                "doc_count": doc_count,
                "docs_errored": docs_errored,
                "docs_successful": docs_successful,
                "failure_reason": failure_reason,
                "submitted": submitted
            }

            # Check for errored jobs
            if any(err in status for err in AIR_REVIEW_ERROR_STATES):
                job_info["level"] = "CRITICAL"
                analysis["failed_jobs"].append(job_info)
                continue

            # Check for high error rate (only for completed or in-progress jobs with results)
            if doc_count > 0 and (docs_errored + docs_successful) > 0:
                error_rate = docs_errored / doc_count
                if error_rate >= error_rate_high:
                    job_info["error_rate"] = round(error_rate * 100, 1)
                    job_info["level"] = "HIGH"
                    analysis["high_error_rate_jobs"].append(job_info)
                elif error_rate >= error_rate_warning:
                    job_info["error_rate"] = round(error_rate * 100, 1)
                    job_info["level"] = "WARNING"
                    analysis["high_error_rate_jobs"].append(job_info)

            # Check for stuck jobs (in progress for too long)
            if "in progress" in status and submit_time:
                hours_running = (now - submit_time).total_seconds() / 3600

                # Estimate expected duration (if available) or use 4 hours as baseline
                expected_hours = 4
                if estimated_run:
                    try:
                        # Estimated run time might be in minutes or as a string
                        if isinstance(estimated_run, (int, float)):
                            expected_hours = estimated_run / 60
                    except (ValueError, TypeError):
                        pass

                if hours_running >= expected_hours * stuck_high:
                    job_info["hours_running"] = round(hours_running, 1)
                    job_info["expected_hours"] = round(expected_hours, 1)
                    job_info["level"] = "HIGH"
                    analysis["stuck_jobs"].append(job_info)
                elif hours_running >= expected_hours * stuck_warning:
                    job_info["hours_running"] = round(hours_running, 1)
                    job_info["expected_hours"] = round(expected_hours, 1)
                    job_info["level"] = "WARNING"
                    analysis["stuck_jobs"].append(job_info)

                analysis["running_jobs"] += 1

            # Check for long queue wait
            elif "queued" in status and submit_time:
                hours_queued = (now - submit_time).total_seconds() / 3600
                if hours_queued >= queue_warning_hours:
                    job_info["hours_queued"] = round(hours_queued, 1)
                    job_info["level"] = "WARNING"
                    analysis["long_queue_jobs"].append(job_info)

            elif "completed" in status:
                analysis["completed_jobs"] += 1

        return analysis

    def analyze_air_privilege_projects(self, projects: List[Dict], workspace_name: str) -> Dict[str, Any]:
        """Analyze aiR for Privilege projects for pipeline failures."""
        analysis = {
            "job_type": "aiR for Privilege",
            "workspace": workspace_name,
            "total_projects": len(projects),
            "failed_projects": [],
            "blocked_projects": [],
            "stale_annotation_projects": [],
            "in_progress_projects": 0,
            "completed_projects": 0
        }

        now = datetime.now(timezone.utc)
        lookback = now - timedelta(hours=self.config.get("lookback_hours", 48))

        stale_warning_hours = self.config.get("privilege_stale_annotation_hours_warning", 24)
        stale_high_hours = self.config.get("privilege_stale_annotation_hours_high", 48)

        for project in projects:
            name = self.extract_field_value(project, "Name") or "Unknown"
            status = (self.extract_field_value(project, "Status") or "").lower()
            doc_count = self.extract_field_value(project, "Document Count") or 0
            modified = self.extract_field_value(project, "System Last Modified On")

            # Parse modification time
            mod_time = None
            if modified:
                try:
                    mod_time = date_parser.parse(modified)
                    if mod_time.tzinfo is None:
                        mod_time = mod_time.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            # Skip projects older than lookback period
            if mod_time and mod_time < lookback:
                continue

            project_info = {
                "name": name,
                "status": status,
                "workspace": workspace_name,
                "artifact_id": project.get("ArtifactID"),
                "doc_count": doc_count,
                "modified": modified
            }

            # Check for pipeline failures
            if any(err in status for err in AIR_PRIVILEGE_ERROR_STATES):
                project_info["level"] = "CRITICAL"
                analysis["failed_projects"].append(project_info)
                continue

            # Check for blocked projects
            if any(blocked in status for blocked in AIR_PRIVILEGE_BLOCKED_STATES):
                project_info["level"] = "CRITICAL"
                analysis["blocked_projects"].append(project_info)
                continue

            # Check for stale annotations (awaiting annotations for too long)
            if "awaiting" in status and mod_time:
                hours_waiting = (now - mod_time).total_seconds() / 3600
                if hours_waiting >= stale_high_hours:
                    project_info["hours_waiting"] = round(hours_waiting, 1)
                    project_info["level"] = "HIGH"
                    analysis["stale_annotation_projects"].append(project_info)
                elif hours_waiting >= stale_warning_hours:
                    project_info["hours_waiting"] = round(hours_waiting, 1)
                    project_info["level"] = "WARNING"
                    analysis["stale_annotation_projects"].append(project_info)

            # Count in-progress and completed
            if "in progress" in status or "running" in status:
                analysis["in_progress_projects"] += 1
            elif "completed" in status:
                analysis["completed_projects"] += 1

        return analysis

    def determine_alert_level(self, review_analysis: Dict, privilege_analyses: List[Dict]) -> Dict[str, Any]:
        """Determine overall alert level from all analyses."""
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "OK",
            "alert_message": "",
            "review_analysis": review_analysis,
            "privilege_analyses": privilege_analyses,
            "critical_issues": [],
            "high_issues": [],
            "warning_issues": []
        }

        # Collect all issues from aiR for Review
        if review_analysis:
            for job in review_analysis.get("failed_jobs", []):
                result["critical_issues"].append({
                    "type": "aiR for Review - Job Failed",
                    "name": job["name"],
                    "workspace": job["workspace"],
                    "reason": job.get("failure_reason", "Unknown")
                })

            for job in review_analysis.get("high_error_rate_jobs", []):
                if job.get("level") == "HIGH":
                    result["high_issues"].append({
                        "type": "aiR for Review - High Error Rate",
                        "name": job["name"],
                        "workspace": job["workspace"],
                        "error_rate": f"{job.get('error_rate', 0)}%"
                    })
                else:
                    result["warning_issues"].append({
                        "type": "aiR for Review - Elevated Error Rate",
                        "name": job["name"],
                        "workspace": job["workspace"],
                        "error_rate": f"{job.get('error_rate', 0)}%"
                    })

            for job in review_analysis.get("stuck_jobs", []):
                if job.get("level") == "HIGH":
                    result["high_issues"].append({
                        "type": "aiR for Review - Stuck Job",
                        "name": job["name"],
                        "workspace": job["workspace"],
                        "hours_running": job.get("hours_running", 0)
                    })
                else:
                    result["warning_issues"].append({
                        "type": "aiR for Review - Long Running Job",
                        "name": job["name"],
                        "workspace": job["workspace"],
                        "hours_running": job.get("hours_running", 0)
                    })

            for job in review_analysis.get("long_queue_jobs", []):
                result["warning_issues"].append({
                    "type": "aiR for Review - Long Queue Wait",
                    "name": job["name"],
                    "workspace": job["workspace"],
                    "hours_queued": job.get("hours_queued", 0)
                })

        # Collect all issues from aiR for Privilege
        for analysis in privilege_analyses:
            for project in analysis.get("failed_projects", []):
                result["critical_issues"].append({
                    "type": "aiR for Privilege - Pipeline Failed",
                    "name": project["name"],
                    "workspace": project["workspace"],
                    "status": project.get("status", "Unknown")
                })

            for project in analysis.get("blocked_projects", []):
                result["critical_issues"].append({
                    "type": "aiR for Privilege - Project Blocked",
                    "name": project["name"],
                    "workspace": project["workspace"]
                })

            for project in analysis.get("stale_annotation_projects", []):
                if project.get("level") == "HIGH":
                    result["high_issues"].append({
                        "type": "aiR for Privilege - Stale Annotations",
                        "name": project["name"],
                        "workspace": project["workspace"],
                        "hours_waiting": project.get("hours_waiting", 0)
                    })
                else:
                    result["warning_issues"].append({
                        "type": "aiR for Privilege - Awaiting Annotations",
                        "name": project["name"],
                        "workspace": project["workspace"],
                        "hours_waiting": project.get("hours_waiting", 0)
                    })

        # Determine overall level
        if result["critical_issues"]:
            result["level"] = "CRITICAL"
            result["alert_message"] = f"CRITICAL: {len(result['critical_issues'])} aiR job/pipeline failures require immediate attention!"
        elif result["high_issues"]:
            result["level"] = "HIGH"
            result["alert_message"] = f"HIGH: {len(result['high_issues'])} aiR issues require investigation"
        elif result["warning_issues"]:
            result["level"] = "WARNING"
            result["alert_message"] = f"WARNING: {len(result['warning_issues'])} aiR issues to monitor"
        else:
            result["alert_message"] = "All aiR jobs and pipelines healthy"

        return result

    def load_state(self) -> Dict:
        """Load previous state to prevent duplicate alerts."""
        state_file = self.config.get("state_file", "/tmp/air_job_state.json")
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Could not load state file: {e}")
        return {}

    def save_state(self, state: Dict):
        """Save current state for future comparisons."""
        state_file = self.config.get("state_file", "/tmp/air_job_state.json")
        try:
            simplified = {
                "level": state["level"],
                "critical_count": len(state["critical_issues"]),
                "high_count": len(state["high_issues"]),
                "warning_count": len(state["warning_issues"]),
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

        # Alert if new critical/high issues appeared
        prev_critical = previous_state.get("critical_count", 0)
        prev_high = previous_state.get("high_count", 0)
        if len(result["critical_issues"]) > prev_critical:
            return True
        if len(result["high_issues"]) > prev_high:
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
            msg['Subject'] = f"[{result['level']}] Relativity aiR Job Alert"

            # Build issues list
            critical_list = "\n".join([
                f"  - [{i['type']}] {i['name']} ({i['workspace']})"
                for i in result.get('critical_issues', [])
            ]) or "  None"

            high_list = "\n".join([
                f"  - [{i['type']}] {i['name']} ({i['workspace']})"
                for i in result.get('high_issues', [])
            ]) or "  None"

            body = f"""
Relativity aiR Job Monitor Alert

Level: {result['level']}
Message: {result['alert_message']}

CRITICAL ISSUES ({len(result['critical_issues'])}):
{critical_list}

HIGH ISSUES ({len(result['high_issues'])}):
{high_list}

Timestamp: {result['timestamp']}

---
This is an automated alert from the Relativity aiR Job Monitor.
See RUNBOOK-AIR-001 (aiR for Review) and RUNBOOK-AIR-002 (aiR for Privilege) for response procedures.
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

        # Build issues summary
        issues_summary = []
        for issue in result.get('critical_issues', [])[:3]:
            issues_summary.append(f":red_circle: {issue['type']}: {issue['name']}")
        for issue in result.get('high_issues', [])[:3]:
            issues_summary.append(f":large_orange_circle: {issue['type']}: {issue['name']}")

        if len(result.get('critical_issues', [])) > 3:
            issues_summary.append(f"(+{len(result['critical_issues']) - 3} more critical)")
        if len(result.get('high_issues', [])) > 3:
            issues_summary.append(f"(+{len(result['high_issues']) - 3} more high)")

        payload = {
            "attachments": [{
                "color": color,
                "title": f"aiR Job Alert: {result['level']}",
                "text": result["alert_message"],
                "fields": [
                    {"title": "Critical", "value": str(len(result["critical_issues"])), "short": True},
                    {"title": "High", "value": str(len(result["high_issues"])), "short": True},
                    {"title": "Issues", "value": "\n".join(issues_summary) or "None", "short": False}
                ],
                "footer": "Relativity aiR Job Monitor",
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
            "dedup_key": "relativity-air-jobs",
            "payload": {
                "summary": f"aiR Jobs: {result['alert_message']}",
                "source": "Relativity aiR Job Monitor",
                "severity": severity,
                "custom_details": {
                    "critical_issues": result.get("critical_issues", [])[:10],
                    "high_issues": result.get("high_issues", [])[:10]
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
            "summary": f"aiR Job Alert: {result['level']}",
            "sections": [{
                "activityTitle": f"aiR Job Alert: {result['level']}",
                "facts": [
                    {"name": "Message", "value": result["alert_message"]},
                    {"name": "Critical Issues", "value": str(len(result["critical_issues"]))},
                    {"name": "High Issues", "value": str(len(result["high_issues"]))}
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
            "monitor": "air_job_monitor",
            "level": result["level"],
            "alert_message": result["alert_message"],
            "critical_issues": result["critical_issues"],
            "high_issues": result["high_issues"],
            "warning_issues": result["warning_issues"],
            "timestamp": result["timestamp"]
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logging.info("Webhook notification sent successfully")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send webhook notification: {e}")

    def send_scom(self, result: Dict):
        """Write event to SCOM via Windows Event Log."""
        if not self.scom:
            return

        try:
            check_result = {
                "level": result.get("level", "UNKNOWN"),
                "message": result.get("alert_message", ""),
                "critical_count": len(result.get("critical_issues", [])),
                "high_count": len(result.get("high_issues", [])),
                "warning_count": len(result.get("warning_issues", []))
            }
            self.scom.write_check_result(check_result)
            logging.info("SCOM event written")
        except Exception as e:
            logging.error(f"Failed to write SCOM event: {e}")

    def send_notifications(self, result: Dict):
        """Send all configured notifications."""
        # Always write to SCOM (even for OK status)
        self.send_scom(result)

        if self.dry_run:
            logging.info(f"DRY RUN: Would send {result['level']} alert: {result['alert_message']}")
            return

        self.send_email(result)
        self.send_slack(result)
        self.send_pagerduty(result)
        self.send_teams(result)
        self.send_webhook(result)

    def run(self, check_review: bool = True, check_privilege: bool = True) -> int:
        """Main monitoring loop. Returns exit code based on alert level."""
        logging.info("Starting aiR Job monitoring check...")

        try:
            review_analysis = None
            privilege_analyses = []

            # Check aiR for Review jobs
            if check_review and self.config.get("check_air_review", True):
                logging.debug("Checking aiR for Review jobs...")
                review_jobs = self.query_air_review_jobs()
                review_analysis = self.analyze_air_review_jobs(review_jobs)
                logging.info(f"aiR for Review: {len(review_analysis['failed_jobs'])} failed, "
                           f"{len(review_analysis['high_error_rate_jobs'])} high error rate, "
                           f"{len(review_analysis['stuck_jobs'])} stuck")

            # Check aiR for Privilege projects
            if check_privilege and self.config.get("check_air_privilege", True):
                logging.debug("Checking aiR for Privilege projects...")
                workspaces = self.get_workspaces()

                for ws in workspaces[:50]:  # Limit to first 50 workspaces
                    ws_id = ws.get("ArtifactID")
                    ws_name = self.extract_field_value(ws, "Name") or str(ws_id)

                    if not ws_id:
                        continue

                    projects = self.query_air_privilege_projects(ws_id)
                    if projects:
                        analysis = self.analyze_air_privilege_projects(projects, ws_name)
                        if (analysis["failed_projects"] or analysis["blocked_projects"] or
                            analysis["stale_annotation_projects"]):
                            privilege_analyses.append(analysis)

                total_failed = sum(len(a["failed_projects"]) for a in privilege_analyses)
                total_blocked = sum(len(a["blocked_projects"]) for a in privilege_analyses)
                logging.info(f"aiR for Privilege: {total_failed} failed pipelines, {total_blocked} blocked")

            # Determine overall alert level
            result = self.determine_alert_level(review_analysis, privilege_analyses)

            # Log the result
            logging.info(f"aiR Job Status: {result['level']}")
            logging.info(f"Critical: {len(result['critical_issues'])}, "
                        f"High: {len(result['high_issues'])}, "
                        f"Warning: {len(result['warning_issues'])}")
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
        description="Monitor Relativity aiR Jobs (aiR for Review and aiR for Privilege)"
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
    parser.add_argument(
        "--review-only",
        action="store_true",
        help="Only check aiR for Review jobs"
    )
    parser.add_argument(
        "--privilege-only",
        action="store_true",
        help="Only check aiR for Privilege projects"
    )

    args = parser.parse_args()

    config = load_config(args.config)

    if not config.get("relativity_host"):
        print("ERROR: relativity_host is required")
        sys.exit(1)

    monitor = AirJobMonitor(
        config=config,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    # Determine what to check
    check_review = not args.privilege_only
    check_privilege = not args.review_only

    exit_code = monitor.run(check_review=check_review, check_privilege=check_privilege)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
