# Reveal AI Alerting & Monitoring Framework

## Executive Summary

This document provides a comprehensive alerting and monitoring framework for Reveal AI eDiscovery environments. Unlike RelativityOne's mature API ecosystem, Reveal AI requires **custom polling-based development** for security monitoring—there are no webhooks, no native SIEM connectors, and limited external monitoring endpoints.

This framework addresses these gaps through:
- Custom polling scripts for job monitoring via the NIA API
- API health monitoring via HTTP endpoints
- Session-based authentication with Keycloak
- Multi-channel alerting (Email, Slack, PagerDuty, Teams)

---

## Platform Architecture Overview

### API Layers

| API Layer | Base URL Pattern | Purpose | Authentication |
|-----------|------------------|---------|----------------|
| **Reveal REST API v2** | `https://[instance].revealdata.com/rest/api/` | Core operations, projects, documents | Session token (`incontrolauthtoken` header) |
| **NIA API** | `http://[server]:5566/nia/` | Integration services, job orchestration | Internal service authentication |
| **NexLP API (StoryEngine)** | `https://[server]/StoryEngineWebApi/api/` | AI/ML analytics operations | OAuth 2.0 |
| **Swagger Documentation** | `/rest/api-docs/index.html?urls.primaryName=v2` | Interactive API reference | Instance authentication |

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    REVEAL AI AUTHENTICATION                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. POST /api/v2/login                                          │
│     ├── username/password                                        │
│     └── Returns: loginSessionId                                  │
│                                                                  │
│  2. Subsequent requests use:                                     │
│     └── Header: incontrolauthtoken: {loginSessionId}            │
│                                                                  │
│  Identity Broker: Keycloak                                       │
│     └── Supports: OAuth 2.0, SAML 2.0, OpenID Connect           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Critical Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **No Webhooks** | All monitoring must poll | Implement scheduled polling at appropriate intervals |
| **No Native SIEM Connectors** | No Splunk/Sentinel/Datadog integration | Custom polling scripts with SIEM-compatible output |
| **No Public Status Page** | Cannot monitor platform health externally | Poll `/nia/version` endpoint directly |
| **No Dedicated Audit API** | Security monitoring via report exports | Scheduled extraction of User Login/Document History reports |
| **Rate Limits Undocumented** | Risk of throttling | Conservative polling intervals, vendor engagement |

---

## Job Status Model (12-State)

The NIA API uses a 12-state status model for all job types. This is the foundation for job monitoring and alerting.

| Status Code | Name | Alert Level | Action |
|-------------|------|-------------|--------|
| 0 | Created | INFO | Log only |
| 1 | Submitted | INFO | Log only |
| 2 | InProcess | MONITOR | Track duration, alert if stuck |
| 3 | Complete | OK | Success confirmation |
| **4** | **Error** | **CRITICAL** | **Immediate alert and investigation** |
| 5 | Cancelled | WARNING | Review cancellation reason |
| 6 | CancelPending | INFO | Monitor for completion |
| **7** | **Deleted** | **AUDIT** | **Compliance tracking required** |
| 8 | Modified | INFO | Change tracking |
| 9-12 | Processing/Deletion States | MONITOR | Alert if stuck |

### Monitorable Job Types

| Job Type | Description | Criticality |
|----------|-------------|-------------|
| AI Document Sync | Clustering, threading, entity extraction | HIGH |
| Index Operations | Search index builds/updates | HIGH |
| Export Jobs | Data exports from projects | CRITICAL (security) |
| Production Jobs | Legal production generation | CRITICAL |
| Bulk Updates | Mass field/tag modifications | HIGH |
| AV Transcription | Audio/video transcription | MEDIUM |
| Deletion Jobs | Document/data removal | CRITICAL (compliance) |

---

## Monitoring Architecture

### Polling-Based Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    REVEAL AI MONITORING ARCHITECTURE             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Polling    │────▶│   Reveal AI  │────▶│    Alert     │    │
│  │   Scripts    │     │     APIs     │     │   Channels   │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                    │                    │             │
│         │              ┌─────┴─────┐              │             │
│         │              │           │              │             │
│         ▼              ▼           ▼              ▼             │
│  ┌──────────────┐ ┌────────┐ ┌─────────┐  ┌──────────────┐    │
│  │ Cron/K8s     │ │REST API│ │ NIA API │  │Email/Slack/  │    │
│  │ Scheduler    │ │  v2    │ │         │  │PagerDuty     │    │
│  └──────────────┘ └────────┘ └─────────┘  └──────────────┘    │
│                                                                  │
│  Data Flow:                                                      │
│  1. Scripts poll APIs at scheduled intervals                    │
│  2. Compare current state to previous state                     │
│  3. Trigger alerts on state changes/thresholds                  │
│  4. Log all checks for audit trail                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Recommended Polling Schedule

| Monitor Type | Data Source | Polling Frequency | Rationale |
|--------------|-------------|-------------------|-----------|
| **API Health** | `/nia/version` | Every 1 minute | Critical availability check |
| **Job Failures** | NIA Job API | Every 5 minutes | Catch errors quickly |
| **Long-Running Jobs** | NIA Job API | Every 15 minutes | Detect stuck jobs |
| **Export Activity** | REST API v2 | Every 15 minutes | Security monitoring |
| **Bulk Operations** | NIA API | Every 10 minutes | Compliance tracking |
| **User Authentication** | Login Report Export | Every 1 hour | Security audit |
| **Document Access** | Document History | Every 30 minutes | Data access monitoring |
| **Reviewer Activity** | Tagging Reports | Every 4 hours | Productivity tracking |

---

## Alert Severity Matrix

### Severity Definitions

| Severity | Response SLA | Description | Examples |
|----------|--------------|-------------|----------|
| **CRITICAL** | Immediate (15 min) | Business-impacting failure | API down, job errors, large exports |
| **HIGH** | 1 hour | Significant issue requiring attention | Long-running jobs, bulk deletions |
| **MEDIUM** | 4 hours | Issue to investigate | Cancelled jobs, unusual activity |
| **LOW** | Next business day | Informational, trend monitoring | Performance metrics |

### Alert Conditions by Monitor

| Condition | Severity | Threshold |
|-----------|----------|-----------|
| API Health Check Failed | CRITICAL | Non-200 response or timeout >5s |
| Job Status = Error (4) | CRITICAL | Any job in error state |
| Job Status = InProcess (2) | HIGH | Duration > 4 hours |
| Job Status = InProcess (2) | CRITICAL | Duration > 24 hours |
| Job Status = Cancelled (5) | MEDIUM | Any cancelled job |
| Job Status = Deleted (7) | HIGH | Compliance tracking |
| Large Export | CRITICAL | >10,000 documents |
| Large Export | HIGH | >1,000 documents |
| Bulk Deletion | CRITICAL | Any mass delete operation |
| Multiple Failed Logins | HIGH | >5 failures in 15 minutes |
| After-Hours Activity | HIGH | Export/deletion outside business hours |

---

## Implementation Tiers

### Tier 1: Critical Monitoring (Immediate)

**Focus:** Job failures and API availability

| Component | Implementation |
|-----------|----------------|
| API Health Monitor | HTTP GET to `/nia/version` every 1 minute |
| Job Failure Monitor | Poll NIA job status, alert on Status=4 |
| Export Monitor | Track export jobs via REST API |

**Development Effort:** 8-16 hours

### Tier 2: Security Monitoring (Week 1-2)

**Focus:** User activity and data access

| Component | Implementation |
|-----------|----------------|
| User Login Tracking | Scheduled export of User Login Report |
| Document Access | Poll Document History API/export |
| Bulk Operations | Monitor bulk update jobs |

**Development Effort:** 16-24 hours

### Tier 3: Compliance & Analytics (Week 3-4)

**Focus:** Audit trails and advanced monitoring

| Component | Implementation |
|-----------|----------------|
| Keycloak Integration | Direct audit log access (if available) |
| Reviewer Metrics | Tagging report analysis |
| Trend Analysis | Historical job performance |

**Development Effort:** 16-20 hours

**Total Estimated Effort:** 40-60 hours

---

## Security Considerations

### Authentication Security

- Store credentials in environment variables or secure vault
- Use service accounts with minimal required permissions
- Rotate session tokens regularly
- Monitor for authentication failures

### Network Security

- All API calls over HTTPS
- Restrict monitoring server access
- Use VPN for on-premise deployments
- Log all API interactions

### Data Handling

- Do not store sensitive document content
- Mask PII in logs and alerts
- Retain monitoring data per compliance requirements
- Encrypt state files at rest

---

## Comparison with RelativityOne

| Capability | Reveal AI | RelativityOne |
|------------|-----------|---------------|
| Webhooks | ❌ Not available | ✅ Supported |
| Native SIEM Connectors | ❌ Not available | ✅ Splunk, Sentinel |
| Audit API | ❌ Export only | ✅ Dedicated API |
| Public Status Page | ❌ Not available | ✅ Available |
| Rate Limit Documentation | ❌ Not documented | ✅ Documented |
| Push Notifications | ❌ Not available | ✅ Available |
| Development Effort | 40-60 hours | 8-16 hours |

---

## Vendor Engagement

For enhanced monitoring capabilities, contact Reveal Data support (support@revealdata.com) to request:

1. Complete REST API documentation including audit endpoints
2. Enterprise logging options not in public documentation
3. Rate limit specifications for polling design
4. Roadmap for webhook or SIEM connector development
5. Access to non-public API documentation

---

## Related Documentation

- [Reveal AI Runbooks](runbooks/README.md)
- [Reveal AI Monitoring Scripts](scripts/README.md)
- [Main Alerting Framework](../eDiscovery_Alerting_Framework.md)

---

## Document Information

| Attribute | Value |
|-----------|-------|
| **Version** | 1.0 |
| **Last Updated** | 2024-11-29 |
| **Platform** | Reveal AI |
| **Coverage** | Job Monitoring, API Health, Security, Exports |
