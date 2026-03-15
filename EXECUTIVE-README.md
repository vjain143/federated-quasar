# Governance Execution Engine (GEX): Executive Flow

## 1) Executive Summary

This platform provides a single governed pipeline for:

1. creating data assets in Trino using dbt,
2. publishing technical and business metadata into OpenMetadata,
3. converting metadata into access policies through Moat + OPA,
4. enforcing those policies at query time in Trino.

The result is a unified operating model where **data creation, metadata quality, and access governance move together** in one auditable flow.

## 2) Business Outcomes

- Faster onboarding of analytics assets with reduced manual handoffs.
- Higher governance confidence through policy decisions derived from metadata.
- Better auditability through run history, step logs, and deterministic sequence.
- Scalable operating pattern for platform, governance, and security teams.

## 3) End-to-End Sequence

### Step 1: Project Intake

An engineer or analyst opens **Governance Execution Engine (GEX) UI** and loads a local dbt project folder.

### Step 2: Model Selection and Run

User selects model and presses **Play**.
The run is tracked with run ID, status, timing, and step logs in the bottom console.

### Step 3: Data Asset Creation in Trino

Governance Execution Engine (GEX) executes:

1. `dbt run`
2. `dbt test`
3. `dbt docs generate`

This creates/updates the target table in Trino.

### Step 4: Metadata Publication in OpenMetadata

The same run then executes two ingestions:

1. Trino metadata ingestion (service/schema/table context)
2. dbt artifact ingestion (manifest/catalog/run results, tags, metadata)

OpenMetadata becomes the canonical metadata source for technical + business context.

### Step 5: Metadata-to-Policy Translation

Moat pulls metadata and attributes from OpenMetadata and maps them to policy inputs.

### Step 6: Policy Distribution to OPA

Moat builds and publishes bundle data consumed by OPA.

### Step 7: Runtime Enforcement in Trino

Trino sends authorization checks to OPA.
OPA evaluates policy using bundle state sourced from metadata and returns allow/deny decisions.

## 4) System Responsibilities

| System | Primary Responsibility |
| --- | --- |
| Governance Execution Engine (GEX) | User control plane, run orchestration, logs/history |
| dbt | Data transformation and model semantics |
| Trino | Data execution engine and query surface |
| OpenMetadata | Metadata system of record |
| Moat | Metadata-to-policy mapping and bundle generation |
| OPA | Real-time policy evaluation for Trino |
| Kestra (optional) | Scheduled/event-driven orchestration trigger |

## 5) Control and Audit Points

The flow provides clear evidence at each stage:

1. Run ID + status timeline in Governance Execution Engine (GEX).
2. dbt stdout/stderr and step-level command logs.
3. Table existence and query validation in Trino.
4. Tag/metadata verification in OpenMetadata.
5. Resource attributes present in Moat.
6. Bundle data available in OPA.
7. Trino authorization calls against OPA decision endpoints.

## 6) Operating Modes

- **Interactive Mode (UI-first):** Load folder, select model, Play/Stop, inspect logs.
- **Automated Mode (Kestra):** Trigger same backend flow for repeatable operations.

Both modes use the same execution engine and metadata/policy chain.

## 7) Leadership KPI View

Recommended executive metrics:

1. End-to-end run success rate.
2. Mean run duration (model run to metadata completion).
3. Policy coverage rate (tables with metadata-derived policy attributes).
4. Authorization decision latency (Trino -> OPA).
5. Number of manual intervention tickets per release.

## 8) Why This Matters

This architecture closes the gap between data engineering and security governance.
Instead of building data first and governing later, governance becomes part of the same delivery path with evidence and enforcement built in.
