# NexLP/Brainspace Platform Investigation

> **Status:** Not Started
> **Priority:** MEDIUM
> **Investigator:** TBD
> **Last Updated:** December 2, 2025

---

## Platform Overview

### What is NexLP/Brainspace?

| Field | Value |
|-------|-------|
| **Vendor** | Reveal (formerly Brainspace) |
| **Deployment** | On-premises |
| **Current Monitoring** | SCOM (Heartbeat, CPU, RAM only) |
| **Kirkland Usage** | eDiscovery analytics |

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

NexLP/Brainspace uses the same underlying technology as Reveal AI (cloud), which has:
- NIA (Natural Intelligence API) - Limited capabilities
- REST API v2 - Document/project operations

### API Availability

| Question | Answer | Source |
|----------|--------|--------|
| Does on-prem Brainspace have API access? | Likely (NIA) | Reveal AI assessment |
| Same API as Reveal Cloud? | Likely similar | Architecture assumption |
| API documentation URL | | Need vendor confirmation |
| API version | | |

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
| **Option 1:** Adapt Reveal AI scripts | Reuse existing code | May need API validation | ~8-16 hours |
| **Option 2:** Extend SCOM monitoring | Leverage existing infra | Limited to what SCOM can see | ~4-8 hours |
| **Option 3:** Build custom solution | Tailored to on-prem | Higher effort | ~40-60 hours |
| **Option 4:** Defer | No immediate effort | Gaps remain | 0 hours |

### Recommended Approach

```
TBD - Pending:
1. API availability confirmation
2. Dec 2 SCOM expansion call outcomes
3. Reveal support response
```

### Next Steps

1. [ ] Confirm API availability on on-prem Brainspace
2. [ ] Test connectivity from monitoring server
3. [ ] Request Reveal support documentation
4. [ ] Evaluate SCOM expansion options (Dec 2 call)
5. [ ] Prototype script adaptation if API confirmed

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
