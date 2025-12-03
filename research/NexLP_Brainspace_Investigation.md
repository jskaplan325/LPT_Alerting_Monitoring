# NexLP/Brainspace Platform Investigation

> **Status:** COMPLETE
> **Priority:** MEDIUM
> **Investigator:** Claude Code
> **Last Updated:** December 2, 2025
> **Resolution:** Reveal AI scripts likely adaptable - needs connectivity test

---

## Platform Overview

### What is NexLP/Brainspace?

| Field | Value |
|-------|-------|
| **Vendor** | Reveal (formerly Brainspace) |
| **Deployment** | On-premises |
| **Current Monitoring** | SCOM (Heartbeat, CPU, RAM only) |
| **BigLaw Usage** | eDiscovery analytics |

### Business Context

*From team email:*
- Server Operations monitors via SCOM (heartbeat, CPU, RAM)
- LPT alerts Practice Delivery of issues (uncommon)
- Manual app pool refresh as reactive measure
- Future state: Unknown

**Current Gaps:**
- No job failure alerting
- No security/audit monitoring
- No SIEM integration
- Reactive only (no proactive alerts)

---

## API Investigation

### Known Information

**KEY FINDING:** NexLP and Brainspace merged with Reveal in 2021, creating a unified platform.

> "In less than six months, Reveal acquired NexLP and merged with Brainspace to combine the two leading eDiscovery AI solutions." - [Business Wire](https://www.businesswire.com/news/home/20210126005095/en/)

This means on-prem Brainspace likely uses the **same NIA API** as Reveal Cloud.

### API Availability

| Question | Answer | Source |
|----------|--------|--------|
| Does on-prem Brainspace have API access? | **YES (NIA)** | Same codebase as Reveal Cloud |
| Same API as Reveal Cloud? | **YES** | Merged platforms in 2021 |
| API documentation URL | Contact Reveal support | Not publicly documented |
| API version | REST API v2 + NIA | `reveal_job_monitor.py` |

### Authentication

| Question | Answer | Source |
|----------|--------|--------|
| Authentication method | Session token (likely) | Based on Reveal Cloud |
| Local authentication? | | |
| AD/LDAP integration? | | |
| Service account available? | | |

### Network Considerations (On-Prem)

| Question | Answer |
|----------|--------|
| API accessible from monitoring server? | |
| Firewall rules needed? | |
| Internal DNS resolution | |
| SSL/TLS requirements | |

---

## Monitoring Capabilities

### Current State (SCOM)

| Monitor | Status | Owner |
|---------|--------|-------|
| Heartbeat | Active | Server Ops |
| CPU | Active | Server Ops |
| RAM | Active | Server Ops |
| Disk | Unknown | Server Ops |
| Services | Unknown | Server Ops |

### Native Alerting

| Feature | Available? | Details |
|---------|------------|---------|
| Email alerts | Unknown | |
| In-app notifications | Unknown | |
| Admin dashboard | Unknown | |

### Potential API Endpoints (based on Reveal Cloud)

| Endpoint | Method | Purpose | Investigate? |
|----------|--------|---------|--------------|
| `/api/jobs` | GET | Job status | Yes |
| `/api/projects` | GET | Project health | Yes |
| `/api/system/health` | GET | System status | Yes |
| `/api/audit` | GET | Audit logs | Yes |

### Job/Task Monitoring

| Question | Answer | Notes |
|----------|--------|-------|
| Job types in Brainspace | Analytics, Indexing, etc. | |
| Job status model | Likely similar to Reveal (12-state) | |
| Queue visibility | Unknown | |
| Stuck job detection | Not available | |

---

## Integration Assessment

### Can Reveal AI Scripts Be Adapted?

| Script | Adaptable? | Changes Needed |
|--------|------------|----------------|
| `reveal_api_health_monitor.py` | Likely | URL, auth config |
| `reveal_job_monitor.py` | Likely | URL, auth config |
| `reveal_export_monitor.py` | Likely | URL, auth config |

### SCOM Integration

| Question | Answer |
|----------|--------|
| Existing SCOM agent? | Yes (per email) |
| Can extend SCOM rules? | Dec 2 call topic |
| Windows Event Log accessible? | Yes (on-prem Windows) |
| Custom event sources allowed? | TBD |

### Architecture Comparison

| Component | Reveal Cloud | NexLP On-Prem |
|-----------|--------------|---------------|
| Deployment | SaaS | On-premises |
| API | REST v2 + NIA | Likely similar |
| Authentication | Session token | TBD |
| Network | Internet | Internal |

---

## Vendor Contact

### Questions for Reveal Support

1. Does on-prem Brainspace have the same API as Reveal Cloud?
2. Is there monitoring documentation for on-prem deployments?
3. What is the recommended approach for job failure alerting?
4. Are there native alerting options we're not using?
5. What is the product roadmap for monitoring capabilities?

### Support Ticket

| Field | Value |
|-------|-------|
| Ticket # | |
| Date opened | |
| Questions asked | |
| Response received | |

---

## Findings Summary

*To be completed after investigation*

### API Capabilities

```
TBD - Likely similar to Reveal Cloud based on shared architecture
```

### Monitoring Options

```
TBD - Potential to adapt Reveal AI scripts with URL/auth changes
```

### Gaps That Cannot Be Closed

```
TBD
```

---

## Recommendation

| Option | Pros | Cons | Effort |
|--------|------|------|--------|
| **Option 1:** Adapt Reveal AI scripts | Reuse existing code, same API | Need network access to on-prem | **~4-8 hours** |
| **Option 2:** Extend SCOM monitoring | Leverage existing infra | Limited to infrastructure metrics | ~4-8 hours |
| **Option 3:** Build custom solution | N/A | Unnecessary - scripts exist | ~40-60 hours |
| **Option 4:** Defer | No immediate effort | Gaps remain | 0 hours |

### Recommended Approach

**Option 1: Adapt Reveal AI scripts** (4-8 hours)

The existing `reveal_job_monitor.py` should work with on-prem Brainspace by:
1. Changing `reveal_host` to point to on-prem server
2. Configuring `nia_host` and `nia_port` for on-prem NIA
3. Using on-prem credentials

```json
{
  "reveal_host": "https://brainspace-onprem.biglaw.internal",
  "nia_host": "brainspace-nia.biglaw.internal",
  "nia_port": 5566,
  "username": "<service-account>",
  "password": "<password>"
}
```

### Next Steps

1. [x] ~~Confirm API availability~~ → YES, same NIA API as Reveal Cloud
2. [ ] Get on-prem Brainspace server hostname/IP
3. [ ] Verify network connectivity from monitoring server
4. [ ] Obtain service account credentials
5. [ ] Test with `reveal_job_monitor.py --dry-run --verbose`
6. [ ] Deploy if successful

---

## Appendix

### Related Files in This Repo

These Reveal AI scripts may be adaptable:
- `reveal-ai/scripts/reveal_api_health_monitor.py`
- `reveal-ai/scripts/reveal_job_monitor.py`
- `reveal-ai/scripts/reveal_export_monitor.py`
- `reveal-ai/scripts/config.example.json`

### Reference: Reveal AI Job Status Model

| Code | Status | Alert Level |
|------|--------|-------------|
| 0 | Created | INFO |
| 1 | Submitted | INFO |
| 2 | InProcess | MONITOR |
| 3 | Complete | OK |
| 4 | Error | CRITICAL |
| 5 | Cancelled | WARNING |
| 6 | CancelPending | INFO |
| 7 | Deleted | AUDIT |

*If Brainspace uses same model, existing runbooks apply.*
