# RUNBOOK-014: RelativityOne Workspace Health

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Workspace Health Issues |
| **Severity** | HIGH (Unavailable) / MEDIUM (Degraded) / LOW (Monitoring) |
| **Platform** | RelativityOne |
| **Detection** | Workspace Manager API |
| **Response SLA** | High: 30 min / Medium: 4 hours / Low: Next business day |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

```
IF Workspace_Status != "Active" THEN HIGH
IF Workspace_Upgrade_Failed THEN HIGH
IF Resource_Pool_Unavailable THEN HIGH
IF Database_Connection_Error THEN CRITICAL
IF Workspace_Size > storage_threshold THEN MEDIUM
IF User_Count > license_threshold THEN MEDIUM
```

---

## Workspace Health Indicators

| Indicator | Healthy State | Alert Threshold |
|-----------|---------------|-----------------|
| Status | Active | Any other status |
| Database connectivity | Connected | Connection errors |
| Resource Pool | Assigned, available | Unavailable |
| SQL Server | Responsive | Latency issues |
| Storage | Below quota | >80% capacity |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Identify affected workspace(s)
- [ ] Determine user impact
- [ ] Open tracking ticket

### Step 2: Quick Status Check

**Via API:**
```bash
curl -X GET "<host>/Relativity.Rest/API/relativity-environment/v1/workspace/<WORKSPACE_ID>" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -"
```

**Key Fields:**
- Status
- ResourcePool
- SqlServer
- FileRepository

**Record the following:**
- Workspace Name: ________________
- Workspace ID: ________________
- Status: ________________
- Resource Pool: ________________
- SQL Server: ________________
- User Impact: ________________

---

## Investigation Procedures

### Step 3: Check Workspace Details

**Via Workspace Manager API:**
```bash
curl -X GET "<host>/Relativity.Rest/API/relativity-environment/v1/workspace/<WORKSPACE_ID>" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -"
```

**Response fields to examine:**
```json
{
  "ArtifactID": 12345,
  "Name": "Workspace Name",
  "Status": "Active",
  "ResourcePool": {...},
  "SqlServer": {...},
  "FileRepository": {...},
  "CreatedOn": "2024-01-01T00:00:00Z"
}
```

### Step 4: Check Related Infrastructure

1. **Resource Pool:**
   - Navigate to resource pool settings
   - Verify pool is active and available

2. **SQL Server:**
   - Check for database connectivity
   - Review for latency issues

3. **File Repository:**
   - Verify file store accessibility
   - Check storage capacity

### Step 5: Review Recent Changes

Query audit for workspace changes:
```json
{
  "condition": "'Object Type' == 'Workspace' AND 'Timestamp' > '<24_HOURS_AGO>'"
}
```

---

## Resolution Procedures

### Scenario A: Workspace Unavailable

**Symptoms:** Workspace Status != "Active", users cannot access

**Steps:**
1. Identify workspace status:
   - Upgrading: Wait for upgrade completion
   - Disabled: Check why disabled
   - Error: Investigate cause

2. **If upgrade stuck:**
   - Check Workspace Upgrade Manager agent
   - Review upgrade queue
   - Escalate if stuck >1 hour

3. **If disabled:**
   - Check for intentional disable
   - Review admin actions
   - Re-enable if appropriate

4. **If error state:**
   - Review error details
   - Check database connectivity
   - Escalate to Relativity Support

### Scenario B: Database Connectivity Issues

**Symptoms:** Connection errors, slow queries, timeouts

**Steps:**
1. Verify SQL Server status
2. Check for:
   - Network connectivity
   - Database availability
   - Connection pool exhaustion

3. **If RelativityOne (SaaS):**
   - Escalate to Relativity Support
   - They manage database infrastructure

4. **While waiting:**
   - Document symptoms
   - Identify affected users
   - Set user expectations

### Scenario C: Resource Pool Issues

**Symptoms:** Resource pool unavailable or misconfigured

**Steps:**
1. Check resource pool status
2. Verify pool assignment
3. Review pool capacity

**Resolution:**
- If misconfigured: Correct settings
- If capacity issue: Escalate for resource allocation
- If pool down: Escalate immediately

### Scenario D: Storage Capacity Issues

**Symptoms:** Storage usage approaching or exceeding limits

**Steps:**
1. Identify storage usage:
   - Document count
   - File sizes
   - Native file storage
   - Imaging storage

2. **Immediate options:**
   - Delete unnecessary data
   - Archive completed matters
   - Export and remove old productions

3. **For capacity increase:**
   - Contact Relativity for capacity planning
   - Review data retention policies

### Scenario E: Workspace Upgrade Issues

**Symptoms:** Workspace upgrade failed or stuck

**Steps:**
1. Check Workspace Upgrade Manager agent status
2. Review upgrade queue
3. Identify error if failed

**Common upgrade issues:**

| Issue | Cause | Resolution |
|-------|-------|------------|
| Agent disabled | Upgrade Manager off | Re-enable agent |
| Upgrade failed | Compatibility issue | Contact support |
| Stuck in queue | Queue backup | Wait or escalate |

**Important Agents:**
- Workspace Upgrade Manager (single-instance)
- Workspace Delete Manager (single-instance)

---

## Workspace Lifecycle Management

### Workspace States

| State | Meaning | User Impact |
|-------|---------|-------------|
| Active | Normal operation | None |
| Upgrading | System upgrade in progress | Read-only or unavailable |
| Disabled | Manually disabled | No access |
| Pending Delete | Queued for deletion | No access |
| Error | System error | No access |

### Workspace Delete Manager
- Single instance per environment
- Handles workspace cleanup
- If disabled, deletions queue up

### Workspace Upgrade Manager
- Single instance per environment
- Manages version upgrades
- Critical for platform updates

---

## Capacity Monitoring

### Storage Thresholds

| Usage | Status | Action |
|-------|--------|--------|
| <50% | Healthy | Monitor |
| 50-70% | Normal | Plan ahead |
| 70-80% | Warning | Consider cleanup |
| 80-90% | High | Immediate review |
| >90% | Critical | Emergency cleanup |

### Monitoring Queries

**Get Workspace Size (via reports or API):**
- Document count
- Total file size
- Native file storage
- Extracted text storage
- Imaging storage

---

## Escalation Procedures

### When to Escalate

| Condition | Level | Timeframe |
|-----------|-------|-----------|
| Workspace unavailable | Relativity Support | Immediate |
| Database errors | Relativity Support | 15 min |
| Upgrade stuck >1 hour | Relativity Support | 1 hour |
| Storage at capacity | Team Lead | 4 hours |
| Resource pool issues | Relativity Support | 30 min |

### Information for Escalation

- [ ] Workspace ID and name
- [ ] Current status
- [ ] Error messages
- [ ] User impact (number of users affected)
- [ ] Recent changes
- [ ] Relevant agent status

---

## Post-Incident Actions

### Immediate
- [ ] Verify workspace accessible
- [ ] Confirm users can work
- [ ] Document resolution

### Short-term (24 hours)
- [ ] Complete incident report
- [ ] Review configuration
- [ ] Check for similar issues in other workspaces

### Long-term
- [ ] Capacity planning review
- [ ] Update monitoring thresholds
- [ ] Review maintenance schedules

---

## Prevention Measures

### Proactive Monitoring
- Regular workspace status checks
- Storage capacity monitoring
- Agent health verification
- Upgrade status tracking

### Capacity Planning
- Monthly storage review
- Quarterly capacity planning
- Archive completed matters
- Clean up test data

### Maintenance
- Coordinate with Relativity for upgrades
- Plan for maintenance windows
- Communicate with users in advance

---

## API Reference

### Workspace Manager API

```bash
# Get workspace details
GET /Relativity.Rest/API/relativity-environment/{version}/workspace/{workspaceID}

# List all workspaces
GET /Relativity.Rest/API/relativity-environment/{version}/workspaces

# Get workspace status
GET /Relativity.Rest/API/relativity-environment/{version}/workspace/{workspaceID}/status
```

### Query Multiple Workspaces

```bash
POST /Relativity.ObjectManager/{version}/workspace/-1/object/query

{
  "request": {
    "objectType": {"ArtifactTypeID": 8},
    "fields": [
      {"Name": "Name"},
      {"Name": "Status"},
      {"Name": "Resource Pool"},
      {"Name": "SQL Server"}
    ]
  }
}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
