# REVEAL-004: Export & Production Security

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Export/Production Security Alert |
| **Severity** | **CRITICAL** (>10k docs) / **HIGH** (>1k docs) |
| **Platform** | Reveal AI |
| **Detection** | Export Job Monitoring |
| **Response SLA** | 15 minutes (CRITICAL) / 1 hour (HIGH) |
| **Escalation** | On-call → Security Team → Legal |

---

## Alert Conditions

```
IF export_document_count > 10000 THEN CRITICAL
IF export_document_count > 1000 THEN HIGH
IF export_initiated_after_hours THEN HIGH
IF export_by_unauthorized_user THEN CRITICAL
IF production_export_to_external_destination THEN CRITICAL
IF export_of_privileged_documents THEN CRITICAL
```

### Export Types to Monitor

| Export Type | Risk Level | Alert Threshold |
|-------------|------------|-----------------|
| Production Export | HIGH | Any to external destination |
| Native Export | MEDIUM | > 1,000 documents |
| Load File Export | MEDIUM | > 1,000 documents |
| Document Download | LOW | > 100 documents in bulk |
| Print | LOW | > 50 documents |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge immediately
- [ ] Treat as potential data exfiltration until cleared
- [ ] Note the export job ID and user

### Step 2: Gather Critical Information

**Record immediately:**
- Export Job ID: ________________
- User Who Initiated: ________________
- Document Count: ________________
- Export Type: ________________
- Destination: ________________
- Project/Case: ________________
- Time of Export: ________________
- Is this during business hours? Yes / No

### Step 3: Quick User Verification
- Is this user authorized to export from this project?
- Is this export expected (known activity)?
- Check with project manager if available

---

## Investigation Procedures

### Step 4: Query Export Details

**Via REST API v2:**
```bash
curl -X GET "https://[instance].revealdata.com/rest/api/v2/projects/{projectId}/exports/{exportId}" \
  -H "incontrolauthtoken: {token}"
```

**Capture:**
- Full export parameters
- Document selection criteria
- Export destination
- User permissions

### Step 5: Verify User Authorization

**Check user's role:**
```bash
curl -X GET "https://[instance].revealdata.com/rest/api/v2/users/{userId}" \
  -H "incontrolauthtoken: {token}"
```

**Verify:**
- [ ] User has export permissions on this project
- [ ] User's role allows this export type
- [ ] User is still active employee
- [ ] Export aligns with user's responsibilities

### Step 6: Review Export Contents

**Critical questions:**
- What documents are being exported?
- Are privileged documents included?
- Are documents subject to protective order included?
- Is this a complete project export or subset?

### Step 7: Check for Suspicious Patterns

| Pattern | Risk Level | Action |
|---------|------------|--------|
| First-time large export by user | HIGH | Verify with manager |
| Export after termination notice | CRITICAL | Block immediately |
| Export outside normal hours | HIGH | Verify legitimacy |
| Export to personal device/location | CRITICAL | Block and investigate |
| Multiple large exports in short period | HIGH | Review pattern |

---

## Resolution Procedures

### Scenario A: Authorized Export (Clear)

**Confirmation obtained:** Export is legitimate business activity

**Actions:**
1. Document authorization confirmation
2. Note approver name and time
3. Close alert as "Verified Authorized"
4. No further action needed

### Scenario B: Suspicious - Need Verification

**Cannot immediately confirm authorization**

**Actions:**
1. **Do NOT block yet** (may be legitimate)
2. Contact user's manager
3. Contact project manager
4. Document verification attempts
5. Escalate to Security if cannot verify within 30 minutes

### Scenario C: Unauthorized Export - Block

**Confirmed unauthorized or high-risk export**

**Immediate Actions:**
1. **Block/Cancel the export if possible**
   ```bash
   curl -X POST "https://[instance].revealdata.com/rest/api/v2/exports/{exportId}/cancel" \
     -H "incontrolauthtoken: {token}"
   ```
2. **Disable user account if severe risk**
3. Preserve all evidence
4. Escalate to Security Team immediately
5. Document all actions taken

### Scenario D: After-Hours Export

**Export initiated outside business hours**

**Actions:**
1. Attempt to reach user directly
2. If cannot reach, contact manager
3. If high-risk indicators present:
   - Consider blocking export
   - Escalate to Security
4. Document timeline

### Scenario E: Production to External Destination

**Production exported to external party**

**Actions:**
1. Verify recipient is authorized
2. Confirm proper chain of custody
3. Check for protective order compliance
4. Document approval chain
5. If unauthorized, block and escalate to Legal

---

## Escalation Procedures

### Security Escalation Triggers

| Condition | Escalation |
|-----------|------------|
| Cannot verify authorization | Security Team |
| User account terminated/notice | Security Team + HR |
| Export to competitor/personal | Security Team + Legal |
| Privileged documents exported | Legal |
| Protective order violation | Legal immediately |

### Escalation Contacts

| Role | Contact | When |
|------|---------|------|
| Security Team | [security contact] | Suspected data theft |
| Legal Team | [legal contact] | Privilege/compliance issues |
| HR | [hr contact] | Employee-related issues |
| Project Manager | [pm contact] | Authorization verification |

---

## Post-Incident Actions

### For Authorized Exports
- [ ] Document verification in ticket
- [ ] Update user profile if first large export
- [ ] Close alert

### For Blocked/Suspicious Exports
- [ ] Preserve all logs and evidence
- [ ] Complete security incident report
- [ ] Work with HR/Legal as needed
- [ ] Review user's historical activity
- [ ] Implement additional controls if needed

### For Compliance Events
- [ ] Document chain of custody
- [ ] Notify appropriate parties per protocol
- [ ] Update compliance tracking
- [ ] Review protective order requirements

---

## Prevention Measures

### Access Controls
- Implement role-based export permissions
- Require approval for large exports
- Restrict export destinations
- Implement DLP controls

### Monitoring Recommendations

| Check | Frequency | Alert Threshold |
|-------|-----------|-----------------|
| Export Jobs | Every 15 minutes | > 1,000 documents |
| Production Exports | Every 15 minutes | Any to external |
| After-Hours Exports | Real-time | Any export |
| User Export Patterns | Daily | Anomalies |

### Policy Recommendations
- Define acceptable export thresholds
- Require manager approval for large exports
- Log all export activities
- Regular access reviews

---

## Document History Tracking

For forensic purposes, track:
```bash
# Get document access history
curl -X GET "https://[instance].revealdata.com/rest/api/v2/documents/{docId}/history" \
  -H "incontrolauthtoken: {token}"
```

This provides:
- Who viewed the document
- When it was accessed
- What actions were taken
- Download/print history

---

## API Reference

### List Exports
```bash
GET https://[instance].revealdata.com/rest/api/v2/projects/{projectId}/exports
```

### Get Export Details
```bash
GET https://[instance].revealdata.com/rest/api/v2/exports/{exportId}
```

### Cancel Export
```bash
POST https://[instance].revealdata.com/rest/api/v2/exports/{exportId}/cancel
```

### Get User Details
```bash
GET https://[instance].revealdata.com/rest/api/v2/users/{userId}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
