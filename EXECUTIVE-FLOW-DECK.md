# Slide 1: Title
Governance Execution Engine (GEX)  
Data Creation + Metadata + Access Governance in One Flow

# Slide 2: Executive Problem
- Data assets are often created before governance is applied.
- Metadata, policy, and enforcement are managed in separate systems.
- This creates audit gaps and operational delays.

# Slide 3: Executive Solution
- One orchestrated pipeline:
  1. Build data in Trino with dbt.
  2. Publish metadata to OpenMetadata.
  3. Translate metadata to policy via Moat.
  4. Enforce policy in Trino via OPA.

# Slide 4: Flow Sequence
1. Load dbt project in Governance Execution Engine (GEX).
2. Select model and run (Play).
3. dbt run/test/docs executes on Trino.
4. Metadata ingested to OpenMetadata.
5. Moat pulls metadata and creates policy bundle.
6. OPA serves decisions for Trino authorization.

# Slide 5: Platform Components
- Governance Execution Engine (GEX): control plane + logs
- Trino: query and data execution
- dbt: model logic + tests
- OpenMetadata: metadata record
- Moat: metadata-to-policy conversion
- OPA: policy decision engine
- Kestra: optional scheduled orchestration

# Slide 6: Control Points
- Run IDs and step logs per execution
- Table creation validation in Trino
- Metadata/tag validation in OpenMetadata
- Bundle validation in OPA
- Decision-path validation in Trino

# Slide 7: Business Impact
- Faster governed delivery of data assets
- Fewer manual governance steps
- Stronger compliance posture with evidence trail
- Repeatable operating model across teams

# Slide 8: KPI Dashboard
- Run success rate
- End-to-end cycle time
- Metadata completeness rate
- Policy coverage percentage
- OPA decision latency

# Slide 9: Operating Modes
- UI-first interactive operations for analysts/engineers
- Kestra-driven automation for scheduled/triggered pipelines
- Same backend path for consistency

# Slide 10: Executive Ask
- Approve rollout of Governance Execution Engine (GEX) as standard entry point
- Track KPIs monthly at platform steering review
- Expand metadata-to-policy coverage by domain in phased adoption
