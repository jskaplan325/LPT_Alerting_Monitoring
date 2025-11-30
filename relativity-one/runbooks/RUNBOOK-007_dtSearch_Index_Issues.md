# RUNBOOK-007: RelativityOne dtSearch Index Issues

## Alert Overview

| Attribute | Value |
|-----------|-------|
| **Alert Name** | dtSearch Index Issues |
| **Severity** | HIGH (Build Error) / MEDIUM (Fragmentation) / WARNING (Performance) |
| **Platform** | RelativityOne |
| **Detection** | Object Manager API (dtSearch Index RDO) |
| **Response SLA** | High: 1 hour / Medium: 4 hours / Warning: Next business day |
| **Escalation** | On-call → Team Lead → Relativity Support |

## Alert Conditions

```
IF Status == "Build Error" THEN HIGH
IF Status == "Compression Error" THEN HIGH
IF Fragmentation_Level > threshold (displayed in red) THEN MEDIUM
IF Build_Duration > expected_threshold THEN WARNING
IF Worker_Status == "Service not responding" THEN CRITICAL
```

---

## dtSearch Index Status Reference

| Status | Meaning | Alert Level |
|--------|---------|-------------|
| Active | Index ready for searching | None |
| Building | Index being built/updated | Info (monitor duration) |
| Build Error | Build failed | **HIGH** |
| Compression Error | Compression operation failed | **HIGH** |
| Inactive | Index not currently usable | Warning |

## Key Metrics

| Metric | Description | Threshold |
|--------|-------------|-----------|
| Fragmentation Level | Index fragmentation % | Red = needs attention |
| Index Size | Size on disk | Monitor for growth |
| Document Count | Documents in index | Match expected |
| Last Build Date | When last updated | Should be recent |

---

## Initial Triage (0-5 minutes)

### Step 1: Acknowledge Alert
- [ ] Acknowledge in monitoring system
- [ ] Note workspace ID and index name
- [ ] Open tracking ticket

### Step 2: Quick Status Check

**Via UI:**
1. Navigate to affected workspace
2. Go to **Search Indexes** → **dtSearch**
3. Select the affected index
4. Review status and error details

**Via Queue Management:**
1. Navigate to **Queue Management** → **dtSearch**
2. Check indexing status (view only - no mass operations available)

**Record the following:**
- Index Name: ________________
- Workspace ID: ________________
- Status: ________________
- Fragmentation Level: ________________
- Last Build Date: ________________
- Document Count: ________________
- Error Message: ________________

---

## Investigation Procedures (5-20 minutes)

### Step 3: Query dtSearch Index Status via API

```bash
curl -X POST "<host>/Relativity.Rest/api/Relativity.ObjectManager/v1/workspace/<WORKSPACE_ID>/object/query" \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Header: -" \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "objectType": {"Name": "dtSearch Index"},
      "fields": [
        {"Name": "Name"},
        {"Name": "Status"},
        {"Name": "Fragmentation Level"},
        {"Name": "Index Size"},
        {"Name": "Document Count"},
        {"Name": "Last Build Date"}
      ],
      "condition": "'\''Status'\'' IN ['\''Build Error'\'', '\''Compression Error'\'']"
    }
  }'
```

### Step 4: Review Index Details

**Via UI - Current Index Details:**
- Worker status (should show Idle or Running)
- Build progress and statistics
- Error messages if failed

### Step 5: Check dtSearch Agent Status

1. Navigate to **Agents** tab
2. Filter for "dtSearch"
3. Verify agent status:
   - Enabled
   - Running or Idle
   - Recent last activity

**Note:** dtSearch Index Agents automatically retry network-related errors up to 3 times at 30-second intervals.

### Step 6: Identify Error Category

**Common dtSearch Index Errors:**

| Error Type | Cause | Resolution |
|------------|-------|------------|
| Network timeout | Connectivity issues | Auto-retries (3x), then investigate |
| Disk space | Storage full | Escalate immediately |
| Memory error | Resource exhaustion | May need index optimization |
| Corrupt document | Bad document in index | Identify and exclude |
| Permission error | Access issues | Check service account |

---

## Resolution Procedures

### Scenario A: Build Error

**Symptoms:** Status = "Build Error"

**Steps:**
1. Review error message in index details
2. Check for common causes:

| Cause | Identification | Resolution |
|-------|---------------|------------|
| Network error | "Connection" in error | Wait for auto-retry, then rebuild |
| Corrupt document | Specific doc ID in error | Exclude document, rebuild |
| Resource issue | Memory/disk errors | Escalate to support |
| Agent failure | Agent not responding | Check agent status |

3. **To rebuild index:**
   - Navigate to dtSearch Index
   - Click **Full Build** or **Incremental Build**
   - Monitor build progress

4. **If errors persist:**
   - Check for problematic documents
   - Review index configuration
   - Escalate if infrastructure issue

### Scenario B: Compression Error

**Symptoms:** Status = "Compression Error"

**Steps:**
1. Compression occurs during index optimization
2. Check for:
   - Disk space availability
   - Index corruption
   - Resource constraints

3. **Resolution options:**
   - Rebuild index from scratch
   - If persistent, escalate to Relativity Support

### Scenario C: High Fragmentation

**Symptoms:** Fragmentation Level displayed in red

**Impact:**
- Slower search performance
- Increased resource consumption
- Potential for search inaccuracies

**Steps:**
1. Note current fragmentation level
2. Schedule index compression:
   - Navigate to dtSearch Index
   - Click **Compress Index** (or schedule via automation)
   - This reduces fragmentation

3. **For severe fragmentation:**
   - Consider full rebuild during maintenance window
   - Monitor compression progress

**Best Practice:** Schedule regular compression during off-peak hours

### Scenario D: Index Build Taking Too Long

**Symptoms:** Build in progress for extended period

**Investigation:**
1. Check document count - large indexes take longer
2. Check worker metrics:
   - Memory utilization
   - CPU activity
   - Tasks per minute

3. **Factors affecting build time:**
   - Number of documents
   - Document sizes
   - Server resources
   - Concurrent operations

4. **Options:**
   - Wait (may be normal for large index)
   - Check for stuck worker
   - Reduce concurrent load

### Scenario E: Index Out of Sync

**Symptoms:** Index document count doesn't match expected

**Steps:**
1. Compare index document count vs. workspace document count
2. Check for:
   - Recently added documents not indexed
   - Documents removed but index not updated
   - Build failures that left index incomplete

3. **Resolution:**
   - Run **Incremental Build** to add new documents
   - Run **Full Build** if significantly out of sync
   - Review auto-population settings

---

## Index Management Operations

### Build Types

| Operation | Use Case | Impact |
|-----------|----------|--------|
| Full Build | Complete rebuild | Takes longer, comprehensive |
| Incremental Build | Add new documents | Faster, adds only changes |
| Compress | Reduce fragmentation | Improves performance |

### Scheduling Considerations

- Schedule full builds during off-peak hours
- Large indexes may take hours to build
- Compression should be regular maintenance

---

## dtSearch Agent Behavior

### Automatic Retry Logic
- Network-related errors: Auto-retry up to 3 times
- Retry interval: 30 seconds
- After 3 failures: Manual intervention required

### Agent Status in Index Details
Worker status displays in Current Index Details:
- Idle: No active indexing
- Running: Actively building/compressing
- Error: Check for issues

---

## Performance Optimization

### Index Health Indicators

| Indicator | Healthy | Action Needed |
|-----------|---------|---------------|
| Fragmentation | <30% | >30% schedule compression |
| Build Success | Consistent | Failures = investigate |
| Search Response | <3 sec | Slow = optimize |

### Optimization Steps
1. Regular compression schedule
2. Optimal index size (consider splitting large indexes)
3. Remove unnecessary fields from index
4. Monitor and tune search queries

---

## Escalation Procedures

### When to Escalate

| Condition | Level | Timeframe |
|-----------|-------|-----------|
| Disk space errors | Relativity Support | Immediate |
| Agent "Service not responding" | Relativity Support | Immediate |
| Persistent build errors | Team Lead | 2 hours |
| Severe fragmentation affecting users | Team Lead | 4 hours |
| Index corruption suspected | Relativity Support | 1 hour |

### Information for Escalation

- [ ] Index name and workspace ID
- [ ] Current status and error messages
- [ ] Fragmentation level
- [ ] Document count
- [ ] Agent status
- [ ] Recent changes to workspace/documents
- [ ] User impact description

---

## Post-Incident Actions

### Immediate
- [ ] Verify index is Active and searchable
- [ ] Test search functionality
- [ ] Document resolution

### Short-term (24 hours)
- [ ] Complete incident report
- [ ] Schedule compression if fragmented
- [ ] Review indexing schedule

### Long-term
- [ ] Implement regular compression schedule
- [ ] Monitor fragmentation trends
- [ ] Optimize index configuration

---

## Prevention Measures

### Regular Maintenance
- Schedule weekly or bi-weekly compression
- Monitor fragmentation levels
- Review index growth trends

### Monitoring Recommendations
- Alert on Build Error status
- Alert on fragmentation >50%
- Monitor build duration trends
- Track search response times

### Index Design Best Practices
- Appropriate fields included
- Reasonable index size
- Consider splitting very large indexes
- Document index configuration

---

## API Reference

### Query dtSearch Index Status

```bash
POST /Relativity.Rest/api/Relativity.ObjectManager/{version}/workspace/{workspaceID}/object/query

# Request body for problem indexes
{
  "request": {
    "objectType": {"Name": "dtSearch Index"},
    "fields": [
      {"Name": "Name"},
      {"Name": "Status"},
      {"Name": "Fragmentation Level"}
    ],
    "condition": "'Status' IN ['Build Error', 'Compression Error']"
  }
}
```

### Query for High Fragmentation

```bash
# Query all indexes and filter by fragmentation in application logic
{
  "request": {
    "objectType": {"Name": "dtSearch Index"},
    "fields": [
      {"Name": "Name"},
      {"Name": "Status"},
      {"Name": "Fragmentation Level"}
    ]
  }
}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | - | Initial runbook |
