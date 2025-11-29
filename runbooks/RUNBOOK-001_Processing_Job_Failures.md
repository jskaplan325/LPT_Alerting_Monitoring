# RUNBOOK-001: RelativityOne Processing Job Failures

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | Processing Job Failure |
| **Severity** | CRITICAL |
| **Platform** | RelativityOne |
| **Detection** | Processing Set Manager API |
| **Response SLA** | 15 minutes |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

This runbook is triggered when any of the following conditions are detected:

```
IF InventoryStatus == "Failed" OR "Stopped" THEN CRITICAL
IF DiscoverStatus == "Failed" OR "Stopped" THEN CRITICAL
IF PublishStatus == "Failed" OR "Stopped" THEN CRITICAL
IF EnvironmentErrors != null THEN CRITICAL
IF DataSourceHasJobLevelErrors == true THEN CRITICAL
IF DataSourceHasDocumentLevelErrors == true THEN HIGH
IF Status == "Paused" for > 30 minutes THEN WARNING
```

## Processing Phases Reference

| Phase | Description | Common Failure Causes |
|-------|-------------|----------------------|
| **Inventory** | Scans data sources, identifies files | Permission issues, network connectivity, corrupt containers |
| **Discover** | Extracts metadata, text, identifies file types | Corrupt files, unsupported formats, resource exhaustion |
| **Publish** | Loads documents into workspace | Database issues, storage limits, field mapping errors |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system to prevent duplicate notifications
- [ ] Note the timestamp and workspace ID from the alert
- [ ] Open a tracking ticket/incident

### Step 2: Access RelativityOne
1. Log into RelativityOne admin portal
2. Navigate to **Instance Details** → **Alerts** section
3. Check for related infrastructure alerts (disabled agents, unresponsive servers)

### Step 3: Quick Status Check
1. Go to **Queue Management** tab
2. Locate the **Processing and Imaging** queue
3. Identify the affected processing set and current status

**Record the following:**
- Processing Set Name: ________________
- Workspace ID: ________________
- Current Phase: ________________
- Status: ________________
- Documents Remaining: ________________
- Error Count: ________________

---

## Investigation Procedures (5-20 minutes)

### Step 4: Access Processing Set Details

**Via UI:**
1. Navigate to the affected workspace
2. Go to **Processing** → **Processing Sets**
3. Click on the failed processing set
4. Review the **Processing History** tab

**Via API:**
```bash
curl -X GET "<host>/Relativity.REST/api/Relativity.Processing.Services.IProcessingModule/Processing Set Manager/GetProcessingSetAsync" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{
    "workspaceId": <WORKSPACE_ID>,
    "processingSetId": <PROCESSING_SET_ID>
  }'
```

### Step 5: Identify Error Type

**Check SetState object for status across all phases:**

| Field | Value | Meaning |
|-------|-------|---------|
| `InventoryStatus` | GUID | Check against status GUIDs |
| `DiscoverStatus` | GUID | Check against status GUIDs |
| `PublishStatus` | GUID | Check against status GUIDs |
| `HasRunningJobs` | boolean | false when stuck |
| `EnvironmentErrors` | string | Infrastructure issues |
| `DataSourceHasJobLevelErrors` | boolean | Source-level failures |
| `DataSourceHasDocumentLevelErrors` | boolean | Document-level failures |

### Step 6: Review Error Details

**For Job-Level Errors:**
1. Navigate to **Processing Set** → **Data Sources**
2. Click on the data source with errors
3. Review **Errors** tab for job-level error messages

**For Document-Level Errors:**
1. Navigate to **Processing Set** → **Errors** tab
2. Filter by error type
3. Export error report for analysis

**Common Error Categories:**

| Error Type | Description | Typical Resolution |
|------------|-------------|-------------------|
| `PasswordProtected` | Encrypted files | Obtain passwords, add to password bank |
| `CorruptFile` | File cannot be processed | Document, exclude from processing |
| `UnsupportedFormat` | File type not supported | Convert or exclude |
| `ExtractionError` | Text/metadata extraction failed | Check file integrity, retry |
| `DatabaseError` | SQL connection/timeout | Check database health |
| `StorageError` | File store issues | Verify storage connectivity |
| `AgentError` | Processing agent failure | Check agent status |

### Step 7: Check Processing History

1. Open **Processing History** (auto-refresh available: 30s, 1m, 5m)
2. Identify when the failure occurred
3. Look for patterns (specific file types, sizes, sources)
4. Note any preceding warnings

---

## Resolution Procedures

### Scenario A: Environment Errors Present

**Symptoms:** `EnvironmentErrors` field contains data

**Steps:**
1. Check **Instance Details** → **Alerts** for agent/server issues
2. Verify Processing Agent status:
   - Navigate to **Agents** tab
   - Filter for "Processing" agents
   - Ensure Server Manager agent is running (required for visibility)
3. Check Worker Monitoring tab:
   - Verify workers show "Running" or "Idle" (not "Service not responding")
   - Check memory and CPU utilization
4. If agents are down, contact Relativity Support immediately

**Resolution:**
```
IF Agent_Status == "Disabled" THEN
  - Check if intentional (maintenance)
  - If not, re-enable agent
  - Monitor for 5 minutes

IF Worker_Status == "Service not responding" THEN
  - Escalate to Relativity Support
  - Do NOT attempt restart without vendor guidance
```

### Scenario B: Job-Level Errors

**Symptoms:** `DataSourceHasJobLevelErrors == true`

**Steps:**
1. Navigate to affected Data Source
2. Review job-level error details
3. Common causes and fixes:

| Cause | Identification | Resolution |
|-------|---------------|------------|
| Permission denied | "Access denied" in error | Verify service account permissions to source |
| Network timeout | "Connection timeout" | Check network path, firewall rules |
| Container corrupt | "Unable to open container" | Verify PST/ZIP integrity, re-acquire |
| Exceeded limits | "Maximum file size" | Adjust processing profile or exclude |

4. After addressing root cause:
   - Click **Retry Errors** if available
   - Or cancel and re-run processing set

### Scenario C: Document-Level Errors

**Symptoms:** `DataSourceHasDocumentLevelErrors == true`

**Steps:**
1. Export error report from Processing Set → Errors tab
2. Categorize errors by type
3. Determine acceptable error threshold (typically <1% of total docs)
4. For password-protected files:
   - Navigate to **Processing** → **Password Bank**
   - Add known passwords
   - Retry processing
5. For corrupt/unsupported files:
   - Document in project records
   - Exclude from processing if legally acceptable
   - Consult with legal team if critical documents

### Scenario D: Paused/Stuck Jobs

**Symptoms:** Status shows "Paused" or no progress for extended period

**Steps:**
1. A "Paused" status typically indicates agent issues
2. Check Queue Management for job priority
3. Verify no higher-priority jobs are consuming all resources
4. Options:
   - **Change Priority**: Elevate stuck job priority
   - **Cancel and Retry**: Cancel job, re-run processing
   - **Resume**: If paused intentionally

**Via Queue Management:**
1. Navigate to **Queue Management** → **Processing and Imaging**
2. Select the stuck job
3. Available actions:
   - Cancel
   - Resume
   - Change priority (1=highest, 10=lowest)

---

## Escalation Procedures

### When to Escalate to Relativity Support

| Condition | Action |
|-----------|--------|
| Environment errors persist after agent check | Immediate escalation |
| Worker status "Service not responding" | Immediate escalation |
| Database errors in error log | Escalate within 30 minutes |
| Issue not resolved within 1 hour | Escalate to Tier 2 |
| Recurrent failures (3+ in 24 hours) | Escalate for root cause analysis |

### Escalation Contacts

| Level | Contact | Response Time |
|-------|---------|---------------|
| Tier 1 | On-call engineer | 15 minutes |
| Tier 2 | Team Lead | 30 minutes |
| Tier 3 | Relativity Support (support@relativity.com) | Per SLA |

### Information to Gather Before Escalation

- [ ] Workspace ID and name
- [ ] Processing Set name and ID
- [ ] Exact error messages (screenshots)
- [ ] Timeline of events
- [ ] Processing History export
- [ ] Agent status screenshots
- [ ] Recent changes to environment
- [ ] Size of data source (GB, doc count)

---

## Post-Incident Actions

### Immediate (within 1 hour of resolution)
- [ ] Verify processing has resumed/completed successfully
- [ ] Document resolution in incident ticket
- [ ] Notify affected stakeholders

### Short-term (within 24 hours)
- [ ] Complete incident report
- [ ] Update runbook if new scenarios encountered
- [ ] Review related workspaces for similar issues

### Long-term (within 1 week)
- [ ] Conduct root cause analysis for recurring issues
- [ ] Update monitoring thresholds if false positives occurred
- [ ] Schedule preventive maintenance if infrastructure issues identified

---

## Prevention Measures

### Proactive Monitoring
- Enable Processing History auto-refresh during active jobs
- Set up alerts for jobs exceeding expected duration thresholds
- Monitor agent health daily

### Capacity Planning
- Submit "Incoming Project Details: RelativityOne" form before large projects
- Coordinate with Relativity for Imaging, OCR, Branding, Productions capacity
- Review processing profiles for optimal settings

### Best Practices
- Test processing profiles with sample data before large runs
- Maintain current password bank for common passwords
- Document known problematic file types per client
- Schedule large processing jobs during off-peak hours

---

## API Reference

### Get Processing Set Status
```bash
GET /Relativity.REST/api/Relativity.Processing.Services.IProcessingModule/Processing Set Manager/GetProcessingSetAsync
```

### Get All Processing Sets in Workspace
```bash
GET /Relativity.REST/api/Relativity.Processing.Services.IProcessingModule/Processing Set Manager/GetAllProcessingSetsAsync
```

### Cancel Processing Job
```bash
POST /Relativity.REST/api/Relativity.Processing.Services.IProcessingModule/Processing Set Manager/CancelProcessingSetAsync
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
