# Relativity aiR Alerting & Monitoring Framework

## Executive Summary

This framework provides comprehensive alerting and monitoring for Relativity aiR products, including **aiR for Review** and **aiR for Privilege**. Both products leverage Azure OpenAI's GPT-4 Omni model for AI-powered document analysis and require proactive monitoring due to their LLM-dependent architecture and billing implications.

**Key Finding:** aiR products require polling-based monitoring via the Jobs tab UI or Object Manager API. No dedicated REST API endpoints for aiR job management have been documented, requiring integration through RelativityOne's standard monitoring infrastructure.

---

## Platform Overview

### aiR for Review

| Attribute | Details |
|-----------|---------|
| **Purpose** | AI-powered document relevance analysis using LLM |
| **Model** | Azure OpenAI GPT-4 Omni (November version) |
| **Analysis Types** | Relevance, Key Documents, Issues |
| **Workflow Phases** | Develop → Validate → Apply |
| **Billing** | Per-document charge (regardless of prior processing) |
| **Regional Availability** | 16 regions (US, UK, AU, CA, EU, APAC) |
| **Language Support** | 83 languages evaluated (English primary) |

### aiR for Privilege

| Attribute | Details |
|-----------|---------|
| **Purpose** | AI-powered privilege prediction and classification |
| **Model** | Azure OpenAI GPT-4 Omni |
| **Pipeline Steps** | 6 sequential steps |
| **Brain System** | Universal, Client, Matter (3-tier knowledge retention) |
| **Billing** | Per-document, pay-per-use |
| **Regional Availability** | 14 regions |
| **Language Support** | English optimized (non-English may yield unexpected results) |

---

## Alert Severity Classification

| Severity | Response Time | aiR for Review | aiR for Privilege |
|----------|---------------|----------------|-------------------|
| **CRITICAL** | Immediate (15 min) | Errored job status, API unavailable | Pipeline "Run Failed", blocked project |
| **HIGH** | < 1 hour | High error rate (>10% docs), stuck jobs | "Apply Annotations Failed", validation errors |
| **MEDIUM** | < 4 hours | Cancelling status, extended queue wait | Single-step failures, annotation issues |
| **LOW** | Next business day | Cost overruns, non-English results | Brain sync delays |

---

## aiR for Review Monitoring

### Job Status Reference

| Status | Description | Alert Level |
|--------|-------------|-------------|
| **Not Started** | Job created, not queued | INFO |
| **Queued** | Awaiting processing resources | INFO (WARNING if >2 hours) |
| **In Progress** | Currently being analyzed | INFO (monitor duration) |
| **Completed** | Successfully finished | OK |
| **Cancelling** | Termination in progress | MEDIUM |
| **Errored** | Failed during execution | CRITICAL |

### Job Metrics to Monitor

| Metric | Field | Alert Threshold |
|--------|-------|-----------------|
| **Total Documents** | Doc Count | Baseline comparison |
| **Successful** | Docs Successful | Track completion rate |
| **Pending** | Docs Pending | Monitor for stuck state |
| **Errored** | Docs Errored | >5% = WARNING, >10% = HIGH |
| **Skipped** | Docs Skipped | >1% requires investigation |
| **Queue Wait Time** | Estimated Wait Time | >2 hours = WARNING |
| **Run Duration** | Submitted → Completed Time | >4x estimate = HIGH |

### Alert Rules

```
# Job Failure Detection
IF Job_Status == "Errored" THEN CRITICAL
  → Trigger: RUNBOOK-AIR-001
  → Escalation: Immediate

# High Document Error Rate
IF (Docs_Errored / Doc_Count) > 0.10 THEN HIGH
IF (Docs_Errored / Doc_Count) > 0.05 THEN WARNING
  → Trigger: RUNBOOK-AIR-001

# Stuck Job Detection
IF Job_Status == "In Progress" AND Duration > 4 * Estimated_Run_Time THEN HIGH
IF Job_Status == "Queued" AND Wait_Time > 2 hours THEN WARNING
  → Trigger: RUNBOOK-AIR-001

# Instance Capacity Warning
IF Active_Jobs_Count >= Instance_Volume_Limit * 0.8 THEN WARNING
  → Notification: Capacity planning alert
```

### Monitoring via Object Manager API

```bash
# Query aiR for Review Jobs (instance-level)
curl -X POST "<host>/Relativity.REST/api/Relativity.Objects/workspace/-1/object/query" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "objectType": {"Name": "aiR for Review Job"},
      "fields": [
        {"Name": "Name"},
        {"Name": "Job Status"},
        {"Name": "Doc Count"},
        {"Name": "Docs Successful"},
        {"Name": "Docs Errored"},
        {"Name": "Docs Skipped"},
        {"Name": "Submitted Time"},
        {"Name": "Completed Time"},
        {"Name": "Job Failure Reason"},
        {"Name": "Workspace"}
      ],
      "condition": "",
      "sorts": [{"FieldIdentifier": {"Name": "Submitted Time"}, "Direction": "Descending"}],
      "queryHint": ""
    },
    "start": 0,
    "length": 100
  }'
```

---

## aiR for Privilege Monitoring

### Pipeline Steps Reference

| Step | Order | Run Required | Annotations Required | Typical Duration (50K docs) |
|------|-------|--------------|---------------------|---------------------------|
| **Prepare Project** | 1 | Yes | No | 1-5 minutes |
| **Classify Domains** | 2 | Yes | Yes | 10-20 minutes |
| **Match Equivalent Domains** | 3 | Yes | Yes | 5-10 minutes |
| **Validate Entities** | 4 | Yes | Yes | 15-30 minutes |
| **Confirm Privilege Status** | 5 | No | Yes | Manual review time |
| **Populate Privilege Results** | 6 | Yes | No | 30-58 minutes |

**Performance Baseline:** ~10,700 documents per hour globally

### Pipeline Status Reference

| Status | Description | Alert Level |
|--------|-------------|-------------|
| **Not Started** | Step pending | INFO |
| **Running** | Step in progress | INFO |
| **Completed** | Step successful | OK |
| **Run Failed** | AI analysis failed | CRITICAL |
| **Apply Annotations Failed** | Annotation save failed | HIGH |
| **Awaiting Annotations** | User action required | INFO (WARNING if >24h) |

### Error Code Categories

| Error Code Pattern | Category | Typical Cause | Alert Level |
|-------------------|----------|---------------|-------------|
| `DOC.GET.VLD.*` | Document Validation | Document content issues | HIGH |
| `DOC.PRS.VLD.*` | Document Parsing | Email parsing failures | HIGH |
| `PRP.RUN.VLD.*` | Project Settings | Configuration incomplete | CRITICAL |
| `BRA.PRS.VLD.*` | Brain Configuration | Client Brain misconfigured | HIGH |
| `KNA.PRS.VLD.*` | Known Attorneys | Missing attorney info | HIGH |
| `PCE.PRS.VLD.*` | Privilege Entities | Entity data incomplete | HIGH |
| `PCD.PRS.VLD.*` | Privilege Domains | Domain data incomplete | HIGH |
| `ENT.PRS.VLD.*` | Entity Validation | Entity artifact issues | HIGH |
| `FAILED_TO_VALIDATE_*` | System Error | Contact Relativity Support | CRITICAL |

### Alert Rules

```
# Pipeline Step Failure
IF Pipeline_Step_Status == "Run Failed" THEN CRITICAL
  → Trigger: RUNBOOK-AIR-002
  → Escalation: Immediate

IF Pipeline_Step_Status == "Apply Annotations Failed" THEN HIGH
  → Trigger: RUNBOOK-AIR-002

# Project Blocked
IF Project_Status == "Blocked" THEN CRITICAL
  → Action: May require abandon and restart
  → Trigger: RUNBOOK-AIR-002

# Concurrent Project Violation
IF Error_Code == "PRP.RUN.VLD.6400" THEN HIGH
  → Cause: Another project in progress
  → Action: Complete or abandon existing project

# Stale Annotation Warning
IF Pipeline_Step_Status == "Awaiting Annotations" AND Duration > 24 hours THEN WARNING
  → Notification: Remind annotators to complete work

# Document Validation Errors
IF Error_Code MATCHES "DOC.*.VLD.*" THEN HIGH
  → Action: Review saved search, remove problematic documents
```

### Critical Error Codes Reference

| Error Code | Message | Resolution |
|------------|---------|------------|
| `DOC.GET.VLD.6140` | Document text exceeds 170KB | Remove oversized documents from Saved Search |
| `DOC.GET.VLD.6600` | Documents lack Extracted Text | Remove documents without text content |
| `DOC.GET.VLD.6300` | Saved Search contains zero documents | Verify search criteria |
| `DOC.GET.VLD.3120` | Too many documents in search | Reduce document count or split |
| `PRP.RUN.VLD.6400` | Multiple projects running | Complete existing project first |
| `PRP.RUN.VLD.1600` | Required settings incomplete | Complete General Settings and project Settings |
| `FAILED_TO_VALIDATE_SAVE_ACTION` | System validation failure | Contact Relativity Support |

---

## Polling Schedule

| Monitor | Frequency | Target |
|---------|-----------|--------|
| aiR for Review Jobs (active) | 5 minutes | Job status, error rates |
| aiR for Review Jobs (all) | 15 minutes | Stuck detection, capacity |
| aiR for Privilege Pipeline | 5 minutes | Step status, failures |
| aiR for Privilege Errors | 15 minutes | Error code aggregation |
| Instance Capacity | 30 minutes | Volume limit tracking |

---

## SCOM Integration

### Event ID Mapping

| Monitor | Base ID | OK | WARNING | HIGH | CRITICAL |
|---------|---------|-----|---------|------|----------|
| aiR for Review Jobs | 1600 | 1600 | 1602 | 1603 | 1604 |
| aiR for Privilege Pipeline | 1700 | 1700 | 1702 | 1703 | 1704 |

### Event Source
- `RelativityOne-Monitor` (shared with other RelativityOne monitors)

---

## Notification Triggers

### aiR for Review

| Event | Notification Channels | Runbook |
|-------|----------------------|---------|
| Job Errored | PagerDuty, Slack, Email | RUNBOOK-AIR-001 |
| High Error Rate (>10%) | Slack, Email | RUNBOOK-AIR-001 |
| Stuck Job (>4x estimate) | Slack, Email | RUNBOOK-AIR-001 |
| Capacity Warning (>80%) | Email | Capacity Planning |

### aiR for Privilege

| Event | Notification Channels | Runbook |
|-------|----------------------|---------|
| Run Failed | PagerDuty, Slack, Email | RUNBOOK-AIR-002 |
| Apply Annotations Failed | Slack, Email | RUNBOOK-AIR-002 |
| Project Blocked | PagerDuty, Slack, Email | RUNBOOK-AIR-002 |
| Concurrent Project Conflict | Slack | RUNBOOK-AIR-002 |

---

## Cost Monitoring

### aiR for Review
- Each document run incurs billing regardless of prior processing
- Monitor via **Cost Explorer** in RelativityOne
- Pre-run estimates may exceed actual (cancellations, errors not billed)
- Alert on: Actual > Estimate * 1.2 (20% variance)

### aiR for Privilege
- Usage-based per-document pricing
- Estimates provided before Prepare Project step
- Track actual vs. estimated at project completion

---

## Data Privacy Notes

Both aiR products use Azure OpenAI with the following privacy guarantees:
- Azure OpenAI does **not** retain document data
- Documents stay within organization's RelativityOne instance
- Processing region determined by deployment configuration
- No cross-matter learning (per-document analysis only for aiR for Review)

---

## Implementation Checklist

### Phase 1: Core Monitoring
- [ ] Configure Object Manager queries for aiR for Review Jobs
- [ ] Set up aiR for Privilege pipeline status monitoring
- [ ] Deploy monitoring scripts (air_job_monitor.py)
- [ ] Configure SCOM event sources

### Phase 2: Alerting
- [ ] Configure PagerDuty escalation policies
- [ ] Set up Slack channels for aiR alerts
- [ ] Deploy runbooks RUNBOOK-AIR-001 and RUNBOOK-AIR-002
- [ ] Test alert thresholds with sample failures

### Phase 3: Operational Maturity
- [ ] Establish baseline metrics for job duration and error rates
- [ ] Configure capacity warnings based on instance limits
- [ ] Implement cost monitoring alerts
- [ ] Create operational dashboards

---

## Escalation Contacts

| Level | Contact | Response Time |
|-------|---------|---------------|
| Tier 1 | On-call engineer | 15 minutes |
| Tier 2 | Team Lead | 30 minutes |
| Tier 3 | Relativity Support | Per SLA |

**Relativity Support:** support@relativity.com

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-30 | - | Initial aiR alerting framework |

---

## References

- [aiR for Review Documentation](https://help.relativity.com/RelativityOne/Content/Relativity/aiR_for_Review/aiR_for_Review.htm)
- [Managing aiR for Review Jobs](https://help.relativity.com/RelativityOne/Content/Relativity/aiR_for_Review/Monitoring_aiR_for_Review_jobs.htm)
- [aiR for Privilege Documentation](https://help.relativity.com/RelativityOne/Content/Relativity/aiR_for_Privilege/aiR_for_Privilege.htm)
- [aiR for Privilege Error Dictionary](https://help.relativity.com/RelativityOne/Content/Relativity/aiR_for_Privilege/aiR_for_Privilege_error_dictionary.htm)
- [Project Pipeline Steps](https://help.relativity.com/RelativityOne/Content/Relativity/aiR_for_Privilege/Project_pipeline_steps.htm)
