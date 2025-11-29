# REVEAL-007: Document Access Monitoring

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Document Access Alert |
| **Severity** | **HIGH** (volume/timing anomalies) |
| **Platform** | Reveal AI |
| **Detection** | Document History API / Reports |
| **Response SLA** | 1 hour |
| **Escalation** | On-call → Security Team → Legal |

---

## Alert Conditions

```
IF document_downloads_per_user > 100 in 1_hour THEN HIGH
IF document_views_per_user > 500 in 1_hour THEN HIGH
IF document_prints_per_user > 50 in 1_hour THEN HIGH
IF document_access_after_hours THEN MEDIUM
IF access_to_privileged_documents_unusual THEN HIGH
IF bulk_download_by_contractor THEN CRITICAL
IF zero_activity_expected_user > 8_hours THEN MEDIUM
```

### Access Thresholds

| Action | Warning | High | Critical |
|--------|---------|------|----------|
| Document Views | > 200/hr | > 500/hr | > 1000/hr |
| Document Downloads | > 50/hr | > 100/hr | > 500/hr |
| Document Prints | > 20/hr | > 50/hr | > 200/hr |
| Native File Access | > 25/hr | > 50/hr | > 200/hr |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge the alert
- [ ] Note user and access pattern
- [ ] Check if known review activity

### Step 2: Gather Information

**Record:**
- User: ________________
- Access Type: View / Download / Print / Native
- Volume: ________________
- Time Period: ________________
- Project/Case: ________________
- Time of Activity: ________________
- During Business Hours? Yes / No

### Step 3: Context Check
- Is user currently reviewing?
- Is there a deadline driving activity?
- Is this consistent with their role?

---

## Investigation Procedures

### Step 4: Query Document History

**Via Document History API:**
```bash
curl -X GET "https://[instance].revealdata.com/rest/api/v2/projects/{projectId}/documents/history?userId={userId}&startDate={date}" \
  -H "incontrolauthtoken: {token}"
```

**From Tagging Reports:**
1. Navigate to Reports → Document History
2. Filter by user and date range
3. Export for analysis

### Step 5: Analyze Access Pattern

**Examine:**
- Documents accessed (random vs sequential)
- Document types (sensitive vs routine)
- Access times (business hours vs after-hours)
- Access method (UI vs API)

**Suspicious Patterns:**

| Pattern | Risk | Action |
|---------|------|--------|
| Sequential doc access (1,2,3...) | HIGH | May be scripted |
| All privileged docs | CRITICAL | Verify authorization |
| Random high-volume | MEDIUM | May be legitimate review |
| After-hours bulk access | HIGH | Verify with user |
| External contractor bulk | CRITICAL | Immediate review |

### Step 6: Check User Context

**Verify:**
- [ ] User is assigned to this project
- [ ] User's role permits this access
- [ ] Activity matches assigned work
- [ ] User is active employee

### Step 7: Compare to Baseline

- What's this user's normal access pattern?
- What's typical for similar users?
- Is this deviation significant?

---

## Resolution Procedures

### Scenario A: Legitimate Heavy Review

**Indicators:** Deadline approaching, user assigned to project, normal patterns

**Actions:**
1. Verify with project manager
2. Document justification
3. Close alert as verified
4. Monitor for continued anomalies

### Scenario B: Possible Data Collection

**Indicators:** Unusual volume, after-hours, downloads focused

**Actions:**
1. **Do not alert the user yet**
2. Contact user's manager discreetly
3. Review what was accessed
4. Check if user's status changed (resignation?)
5. Escalate to Security if suspicious
6. Preserve logs

### Scenario C: Confirmed Unauthorized Access

**Evidence of data theft or unauthorized collection**

**Immediate Actions:**
1. **Disable user account**
2. Terminate active sessions
3. Preserve all logs and evidence
4. Assess what was accessed
5. Escalate to Security and Legal
6. Begin incident response

### Scenario D: After-Hours Access

**Access outside normal business hours**

**Actions:**
1. Check if user is known to work late
2. Verify current project deadlines
3. Contact user next business day
4. Document explanation
5. Flag for pattern analysis

### Scenario E: Zero Activity Anomaly

**Expected user showing no activity**

**Actions:**
1. Check if user is on leave
2. Verify system access (can they log in?)
3. Check for technical issues
4. May indicate shared account or issues

---

## Escalation Procedures

### Escalation Triggers

| Condition | Escalate To |
|-----------|-------------|
| Bulk downloads by contractor | Security + Legal |
| Access to privileged docs | Legal |
| After-hours bulk access | Security |
| Suspected data theft | Security + Legal + HR |
| Pattern matching terminating employee | Security + HR |

### Evidence Preservation

When escalating, preserve:
- Complete document history
- User session logs
- Downloaded file list
- Access timestamps
- User account status

---

## Post-Incident Actions

### For Normal Activity
- [ ] Document verification
- [ ] Update baseline if needed
- [ ] Close alert

### For Suspicious Activity
- [ ] Complete investigation
- [ ] Incident report
- [ ] Review user permissions
- [ ] Implement additional monitoring

### For Confirmed Incidents
- [ ] Full forensic investigation
- [ ] Data exposure assessment
- [ ] HR/Legal engagement
- [ ] Policy/control updates

---

## Prevention Measures

### Access Controls
- Role-based document access
- Print/download restrictions where appropriate
- Watermarking for sensitive documents
- External contractor restrictions

### Monitoring
- Real-time access alerting
- Pattern baseline establishment
- After-hours monitoring
- Privileged document tracking

### Behavioral Analytics
- Establish normal baselines
- Detect deviation from normal
- Track access trends
- Identify high-risk patterns

### DLP Integration
- Track sensitive document access
- Monitor bulk operations
- Alert on policy violations

---

## Reviewer Productivity Context

Understanding normal review patterns helps identify anomalies:

| Role | Typical Docs/Day | Typical Hours |
|------|------------------|---------------|
| First-Pass Reviewer | 200-500 | Business hours |
| Senior Reviewer | 50-200 | Business hours |
| QC Reviewer | 100-300 | Business hours |
| Attorney Reviewer | 20-100 | Variable |

Significant deviation from these norms warrants review.

---

## API Reference

### Get Document History
```bash
GET https://[instance].revealdata.com/rest/api/v2/documents/{docId}/history
```

### Get User Activity
```bash
GET https://[instance].revealdata.com/rest/api/v2/projects/{projectId}/activity?userId={userId}
```

### Tagging Reports API
```bash
GET https://[instance].revealdata.com/rest/api/v2/reports/tagging?projectId={projectId}&userId={userId}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
