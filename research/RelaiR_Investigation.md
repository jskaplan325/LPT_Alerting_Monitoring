# RelaiR Platform Investigation

> **Status:** Not Started
> **Priority:** MEDIUM
> **Investigator:** TBD
> **Last Updated:** December 2, 2025

---

## Platform Overview

### What is RelaiR?

| Field | Value |
|-------|-------|
| **Vendor** | Relativity |
| **Deployment** | SaaS |
| **Current Monitoring** | Vendor uptime only |
| **Kirkland Usage** | TBD |

### Business Context

*Document how Kirkland uses this platform, what data resides there, and criticality to operations.*

- [ ] Document primary use cases
- [ ] Identify active workspaces/projects
- [ ] Determine data sensitivity level
- [ ] Assess business criticality (Critical/High/Medium/Low)

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
| **Option 1:** Use native monitoring | | | |
| **Option 2:** Extend existing scripts | | | |
| **Option 3:** Build custom solution | | | |
| **Option 4:** Defer (vendor monitoring sufficient) | | | |

### Recommended Approach

```
TBD - Complete investigation first
```

### Next Steps

1. [ ]
2. [ ]
3. [ ]

---

## Appendix

### Reference Links

- Product page:
- Documentation:
- API reference:
- Status page:

### Related Files in This Repo

- `relativity-one/scripts/air_job_monitor.py` - May be applicable
- `relativity-one/aiR_Alerting_Framework.md` - aiR architecture reference
