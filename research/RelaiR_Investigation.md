# RelaiR Platform Investigation

> **Status:** COMPLETE
> **Priority:** MEDIUM
> **Investigator:** Claude Code
> **Last Updated:** December 2, 2025
> **Resolution:** ALREADY COVERED by existing scripts

---

## Platform Overview

### What is RelaiR?

**FINDING: RelaiR = Relativity aiR** (same product, different spelling/abbreviation)

| Field | Value |
|-------|-------|
| **Vendor** | Relativity |
| **Deployment** | SaaS (part of RelativityOne) |
| **Current Monitoring** | `air_job_monitor.py` ALREADY EXISTS |
| **BigLaw Usage** | 2 workspaces currently using aiR |

### Business Context

Relativity aiR is Relativity's generative AI suite built on Azure OpenAI's GPT-4 Omni model:

| Product | Purpose | Workflow |
|---------|---------|----------|
| **aiR for Review** | Relevance analysis, key document identification, issue categorization | Develop → Validate → Apply |
| **aiR for Privilege** | Privilege prediction and classification | 6-step sequential pipeline |

- [x] Document primary use cases: AI-powered document review and privilege analysis
- [x] Identify active workspaces/projects: 2 workspaces currently (per team email)
- [x] Determine data sensitivity level: HIGH (legal documents)
- [x] Assess business criticality: **CRITICAL** (AI workflow failures affect review timelines)

---

## RESOLUTION: Already Covered

### Existing Script Coverage

The `air_job_monitor.py` script (1,072 lines) already provides comprehensive monitoring:

| Feature | Coverage | Details |
|---------|----------|---------|
| aiR for Review Jobs | ✅ Full | Failed jobs, error rates, stuck jobs, queue waits |
| aiR for Privilege Projects | ✅ Full | Pipeline failures, blocked projects, stale annotations |
| SCOM Integration | ✅ Yes | Event IDs 1600-1604 (Review), 1700-1704 (Privilege) |
| Multi-channel Alerts | ✅ Yes | Email, Slack, PagerDuty, Teams, Webhooks |

### API Endpoints Used

```
aiR for Review:
POST /Relativity.REST/api/Relativity.Objects/workspace/-1/object/query
  objectType: "aiR for Review Job"

aiR for Privilege:
POST /Relativity.REST/api/Relativity.Objects/workspace/{id}/object/query
  objectType: "aiR for Privilege Project"
```

### Job Statuses Monitored

**aiR for Review:**
- Errored → CRITICAL alert
- High error rate (>10%) → HIGH alert
- Stuck (>4x expected time) → HIGH alert
- Long queue (>2 hours) → WARNING alert

**aiR for Privilege:**
- Run Failed → CRITICAL alert
- Apply Annotations Failed → CRITICAL alert
- Blocked → CRITICAL alert
- Awaiting Annotations (>24h) → WARNING alert

---

## API Investigation

### API Availability

| Question | Answer | Source |
|----------|--------|--------|
| Does RelaiR have a public API? | | |
| Is it separate from RelativityOne API? | | |
| API documentation URL | | |
| API version | | |

### Authentication

| Question | Answer | Source |
|----------|--------|--------|
| Authentication method | | |
| OAuth 2.0 supported? | | |
| Service account available? | | |
| API key option? | | |
| Token expiration | | |

### Rate Limits

| Question | Answer | Source |
|----------|--------|--------|
| Rate limit (requests/minute) | | |
| Rate limit (requests/day) | | |
| Retry-After header supported? | | |

---

## Monitoring Capabilities

### Native Alerting

| Feature | Available? | Details |
|---------|------------|---------|
| Email alerts | | |
| Webhook support | | |
| In-app notifications | | |
| Status page | | |
| Vendor alert subscription | | |

### Available Endpoints (if API exists)

| Endpoint | Method | Purpose | Polling Candidate? |
|----------|--------|---------|-------------------|
| | | | |
| | | | |
| | | | |

### Job/Task Monitoring

| Question | Answer | Notes |
|----------|--------|-------|
| Does RelaiR run background jobs? | | |
| Job status endpoint available? | | |
| Job types | | |
| Failure states | | |
| Queue visibility | | |

### Audit/Security

| Feature | Available? | Details |
|---------|------------|---------|
| Audit log API | | |
| Login history | | |
| Export tracking | | |
| Permission changes | | |

---

## Integration Assessment

### Relationship to Existing Solutions

| Question | Answer |
|----------|--------|
| Is RelaiR part of RelativityOne? | |
| Does `air_job_monitor.py` cover RelaiR? | |
| Same Object Manager API? | |
| Shared authentication? | |

### SIEM Integration

| Question | Answer |
|----------|--------|
| Native SIEM connectors? | |
| Splunk app available? | |
| Can write to Windows Event Log? | |
| Syslog support? | |

---

## Vendor Contact

### Support Ticket (if needed)

| Field | Value |
|-------|-------|
| Ticket # | |
| Date opened | |
| Questions asked | |
| Response received | |
| Response date | |

### Documentation Requested

- [ ] API reference documentation
- [ ] Monitoring best practices guide
- [ ] Integration options overview

---

## Findings Summary

*To be completed after investigation*

### API Capabilities

```
TBD
```

### Monitoring Options

```
TBD
```

### Gaps Identified

```
TBD
```

---

## Recommendation

| Option | Pros | Cons | Effort |
|--------|------|------|--------|
| **Option 1:** Deploy existing `air_job_monitor.py` | Already built, tested, documented | None | **0 hours** (just deploy) |

### Recommended Approach

**NO NEW DEVELOPMENT NEEDED.** Deploy existing script.

```bash
# Deploy command
python relativity-one/scripts/air_job_monitor.py --config config.json

# Test first
python relativity-one/scripts/air_job_monitor.py --config config.json --dry-run --verbose
```

### Next Steps

1. [x] ~~Investigate if RelaiR is covered~~ → YES, it's Relativity aiR
2. [ ] Obtain RelativityOne OAuth credentials
3. [ ] Deploy `air_job_monitor.py` to monitoring server
4. [ ] Configure SCOM rules for Event IDs 1600-1704

---

## Appendix

### Reference Links

- Product page: https://www.relativity.com/ediscovery-software/relativityone/
- Documentation: https://platform.relativity.com/RelativityOne/Content/Relativity_Platform/index.htm
- API reference: https://platform.relativity.com/RelativityOne/Content/REST_API/REST_API.htm

### Related Files in This Repo

- `relativity-one/scripts/air_job_monitor.py` - **COVERS RelaiR**
- `relativity-one/aiR_Alerting_Framework.md` - aiR architecture reference
- `relativity-one/runbooks/RUNBOOK-AIR-001_aiR_Review_Failures.md` - aiR for Review runbook
- `relativity-one/runbooks/RUNBOOK-AIR-002_aiR_Privilege_Failures.md` - aiR for Privilege runbook
