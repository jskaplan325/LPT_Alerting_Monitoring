# Gap Closure Plan: Application Monitoring Matrix

> **Created:** December 2, 2025
> **Purpose:** Map repository monitoring assets to identified gaps across eDiscovery platforms
> **Reference:** Team email on Server Monitoring and Alerting (Dec 2025)

---

## Executive Summary

| Platform | Current Gaps | Repo Solution | Effort | Priority |
|----------|--------------|---------------|--------|----------|
| **RelativityOne** | Job failures, Security, Telemetry | 6 scripts ready | Deploy + Configure | HIGH |
| **Reveal Cloud** | Job failures, API health, Exports | 3 scripts ready | Deploy + Configure | HIGH |
| **Relativity Server** | SIEM integration, expanded SCOM | Scripts adaptable | Coordinate with Server Ops | HIGH |
| **NexLP/Brainspace** | Everything beyond heartbeat | None available | Custom development | MEDIUM |
| **RelaiR/ASK/AJII** | Unknown capabilities | None available | Research first | MEDIUM/LOW |

---

## Platform-by-Platform Gap Closure

### 1. RelativityOne (SaaS) - HIGH PRIORITY

**Current State (from email):**
- Vendor uptime monitoring only
- KE manual upness checks
- No proactive job failure alerts
- No SIEM integration
- 2 workspaces currently (both using aiR)

**Identified Gaps:**

| Gap | Impact | Repo Solution | Script |
|-----|--------|---------------|--------|
| Telemetry Agent Monitoring | CRITICAL - User logout if fails | `telemetry_agent_monitor.py` | 1-min polling |
| Job Failure Alerts | HIGH - No visibility into processing/production failures | `job_queue_monitor.py` | 5-min polling |
| Security/Audit Monitoring | HIGH - No brute force or export alerts | `security_audit_monitor.py` | 5-min polling |
| Worker Health | HIGH - No agent status visibility | `worker_health_monitor.py` | 1-min polling |
| Billing Agent | MEDIUM - Compliance risk | `billing_agent_monitor.py` | 1-min polling |
| Native Alert Monitoring | MEDIUM - Platform alerts not forwarded | `alert_manager_monitor.py` | 1-min polling |
| aiR Job Failures | HIGH - AI workflow failures undetected | `air_job_monitor.py` | 5-min polling |
| SIEM Integration | HIGH - No centralized logging | All scripts write to Windows Event Log | SCOM rules provided |

**Deployment Checklist:**

- [ ] Obtain RelativityOne OAuth credentials (Client ID, Secret)
- [ ] Configure `relativity-one/scripts/config.json` with instance URL
- [ ] Register Windows Event Source: `RelativityOne-Monitor`
- [ ] Deploy scripts to monitoring server
- [ ] Configure SCOM management pack rules (see README.md)
- [ ] Set up alert channels (Email, Slack, PagerDuty, Teams)
- [ ] Test with `--dry-run --verbose` flags
- [ ] Schedule via cron/Task Scheduler per recommended intervals
- [ ] Validate alerts reach intended recipients

**Runbooks Available:** 18 (RUNBOOK-001 through RUNBOOK-018) + 2 aiR runbooks

---

### 2. Reveal Cloud (SaaS) - HIGH PRIORITY

**Current State (from email):**
- Vendor uptime monitoring only
- KE manual upness checks
- No client data currently
- Email alerts for unhandled errors only

**Identified Gaps:**

| Gap | Impact | Repo Solution | Script |
|-----|--------|---------------|--------|
| API Health Monitoring | CRITICAL - No NIA/REST availability alerts | `reveal_api_health_monitor.py` | 1-min polling |
| Job Failure Alerts | HIGH - Status=4 errors undetected | `reveal_job_monitor.py` | 5-min polling |
| Stuck Job Detection | HIGH - Long-running jobs block queues | `reveal_job_monitor.py` | Configurable thresholds |
| Export Security | MEDIUM - Large/after-hours exports | `reveal_export_monitor.py` | 15-min polling |
| SIEM Integration | HIGH - No centralized logging | All scripts write to Windows Event Log | SCOM rules provided |

**Deployment Checklist:**

- [ ] Obtain Reveal AI credentials (Username, Password for session token)
- [ ] Configure `reveal-ai/scripts/config.json` with instance URL
- [ ] Register Windows Event Source: `RevealAI-Monitor`
- [ ] Deploy scripts to monitoring server
- [ ] Configure SCOM management pack rules
- [ ] Set up alert channels
- [ ] Test with `--dry-run --verbose` flags
- [ ] Schedule via cron/Task Scheduler
- [ ] Validate alerts reach intended recipients

**Runbooks Available:** 8 (REVEAL-001 through REVEAL-008)

**Note:** Even with no client data currently, deploying monitoring now ensures readiness when workspaces are populated.

---

### 3. Relativity Server (On-Prem) - HIGH PRIORITY

**Current State (from email):**
- SCOM: Heartbeat, CPU, RAM, Relativity services
- Instance Settings configured:
  - `LockoutNotificationList`: josh.haley@kirkland.com;john.delgado@kirkland.com;barry.peters@kirkland.com
  - `CaseStatisticsNotificationList`: Not configured
- LPT: Queue visibility for job blocking
- Custom Pages: Manual app pool recycling after LPT alert

**Identified Gaps:**

| Gap | Impact | Repo Solution | Notes |
|-----|--------|---------------|-------|
| Expanded SCOM Alerting | HIGH - Limited to infrastructure only | Dec 2, 2025 call with Engineering | Scope expansion discussion |
| Job Failure Alerts | MEDIUM - Only LPT queue visibility | Scripts could be adapted | Requires API access validation |
| CaseStatisticsNotificationList | LOW - Not receiving daily telemetry | Configure Instance Setting | Add team distro |
| SIEM Integration | MEDIUM - No centralized event logging | `scom_integration.py` helper | Extend existing SCOM |

**Recommended Actions:**

1. **Immediate (Instance Setting):**
   ```
   CaseStatisticsNotificationList = josh.haley@kirkland.com;john.delgado@kirkland.com;barry.peters@kirkland.com
   ```

2. **Dec 2, 2025 SCOM Call Agenda Items:**
   - Can SCOM monitor Relativity agent status (not just services)?
   - Can SCOM alert on Windows Event Log entries from custom scripts?
   - Can job queue depth be exposed to SCOM?
   - Timeline for expanded monitoring scope

3. **Future (Environment Watch - Server 2024):**
   - Scheduled for January 2024 migration completion
   - Will provide: Alerts, Dashboards, Log searching, Queue visibility
   - Custom pages issue remediated December 13
   - May reduce need for custom scripting

**Runbooks Available:** RelativityOne runbooks can be adapted for on-prem scenarios

---

### 4. NexLP/Brainspace (On-Prem) - MEDIUM PRIORITY

**Current State (from email):**
- SCOM: Heartbeat, CPU, RAM only
- LPT: Alert Practice Delivery of issues (uncommon)
- Manual: App pool refresh, engage Reveal as needed
- Future state: Unknown

**Identified Gaps:**

| Gap | Impact | Current Workaround | Solution Path |
|-----|--------|-------------------|---------------|
| Job Failure Alerts | HIGH | None - reactive only | Needs API investigation |
| Security Monitoring | MEDIUM | None | Unknown if API supports |
| SIEM Integration | MEDIUM | None | Needs API investigation |
| Proactive Health Checks | MEDIUM | Manual app pool refresh | Unknown automation options |

**Research Required:**

- [ ] Document NexLP/Brainspace API capabilities (NIA endpoint?)
- [ ] Identify available job status endpoints
- [ ] Determine authentication method
- [ ] Assess rate limits and polling feasibility
- [ ] Check with Reveal support on monitoring recommendations
- [ ] Evaluate if Reveal Cloud scripts can be adapted

**Recommendation:** Defer custom development until:
1. API capabilities are documented
2. Reveal provides guidance on monitoring options
3. Business case justifies 40-60 hour development effort

---

### 5. RelaiR (SaaS) - MEDIUM PRIORITY

**Current State (from email):**
- Vendor uptime monitoring only
- Part of RelativityOne ecosystem

**Research Required:**

| Question | Status | Action |
|----------|--------|--------|
| Does RelaiR have a separate API? | Unknown | Contact Relativity support |
| Is it covered by RelativityOne monitoring? | Unknown | Check if aiR scripts cover this |
| What job types does RelaiR execute? | Unknown | Review product documentation |
| Are there native alerting options? | Unknown | Check admin console |

**Potential Coverage:** May be partially covered by `air_job_monitor.py` if RelaiR uses same Object Manager APIs as aiR for Review/Privilege.

---

### 6. ASK (SaaS) - LOW PRIORITY

**Current State (from email):**
- Vendor uptime monitoring only

**Research Required:**

| Question | Status | Action |
|----------|--------|--------|
| What is ASK's primary function? | Unknown | Document use case |
| API availability? | Unknown | Contact vendor |
| Integration with other platforms? | Unknown | Architecture review |
| Native monitoring options? | Unknown | Check admin console |

---

### 7. AJII (SaaS) - LOW PRIORITY

**Current State (from email):**
- Vendor uptime monitoring only

**Research Required:**

| Question | Status | Action |
|----------|--------|--------|
| What is AJII's primary function? | Unknown | Document use case |
| API availability? | Unknown | Contact vendor |
| Integration with other platforms? | Unknown | Architecture review |
| Native monitoring options? | Unknown | Check admin console |

---

## Implementation Roadmap

### Phase 1: Quick Wins (Ready to Deploy)

| Action | Platform | Owner | Dependency |
|--------|----------|-------|------------|
| Deploy telemetry_agent_monitor.py | RelativityOne | Practice Delivery | OAuth credentials |
| Deploy air_job_monitor.py | RelativityOne | Practice Delivery | OAuth credentials |
| Deploy reveal_api_health_monitor.py | Reveal Cloud | Practice Delivery | Session credentials |
| Configure CaseStatisticsNotificationList | Rel Server | Practice Delivery | None |
| Attend SCOM expansion call | Rel Server | Server Ops + PD | Dec 2, 2025 |

### Phase 2: Full Deployment

| Action | Platform | Owner | Dependency |
|--------|----------|-------|------------|
| Deploy all 6 RelativityOne scripts | RelativityOne | Practice Delivery | Phase 1 complete |
| Deploy all 3 Reveal AI scripts | Reveal Cloud | Practice Delivery | Phase 1 complete |
| Configure SCOM management pack | Both | Server Ops | Scripts deployed |
| Set up alert channels | Both | Practice Delivery | Scripts deployed |

### Phase 3: Research & Expand

| Action | Platform | Owner | Dependency |
|--------|----------|-------|------------|
| Document RelaiR API capabilities | RelaiR | Practice Delivery | Vendor contact |
| Document ASK/AJII capabilities | ASK/AJII | Practice Delivery | Vendor contact |
| Assess NexLP API options | Brainspace | Practice Delivery | Reveal support |
| Evaluate Environment Watch | Rel Server | Practice Delivery | Jan 2024 migration |

---

## Script-to-Gap Mapping Reference

| Script | Gaps Addressed | Platforms |
|--------|----------------|-----------|
| `telemetry_agent_monitor.py` | Telemetry failure (user logout prevention) | RelativityOne |
| `billing_agent_monitor.py` | Billing compliance | RelativityOne |
| `alert_manager_monitor.py` | Native platform alert forwarding | RelativityOne |
| `worker_health_monitor.py` | Agent/worker status | RelativityOne |
| `job_queue_monitor.py` | Processing/Production/Imaging failures | RelativityOne |
| `security_audit_monitor.py` | Brute force, exports, lockbox, permissions | RelativityOne |
| `air_job_monitor.py` | aiR for Review + Privilege failures | RelativityOne, RelaiR (TBD) |
| `reveal_api_health_monitor.py` | API availability | Reveal Cloud |
| `reveal_job_monitor.py` | Job failures, stuck jobs | Reveal Cloud, Brainspace (TBD) |
| `reveal_export_monitor.py` | Large exports, after-hours activity | Reveal Cloud |
| `scom_integration.py` | Windows Event Log for SCOM | All (helper module) |

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Platforms with job failure alerting | 1 (partial) | 4 | Count of platforms |
| SIEM integration coverage | 0% | 60% | Platforms with Event Log integration |
| Mean time to detect (MTTD) | Hours/Days | Minutes | Time from failure to alert |
| Alert channels configured | 1 (email) | 4 | Email, Slack, PagerDuty, Teams |
| Runbook coverage | 0 | 28 | Documented response procedures |

---

## Appendix: Email Reference Points

Key items from the team email mapped to this plan:

| Email Item | Plan Section |
|------------|--------------|
| SCOM monitoring (heartbeat, CPU, RAM) | Sections 1, 3, 4 |
| LockoutNotificationList configured | Section 3 - noted as complete |
| CaseStatisticsNotificationList not configured | Section 3 - action item |
| Environment Watch (Server 2024) | Section 3 - future state |
| Dec 2, 2025 SCOM call | Section 3 - action item |
| Custom pages fix Dec 13 | Section 3 - noted |
| NexLP future state unknown | Section 4 - research required |
| No client data in Reveal Cloud | Section 2 - noted, deploy anyway |
| 2 workspaces in RelOne with aiR | Section 1 - prioritize aiR monitoring |
