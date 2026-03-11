Below is the entire PPT content in Markdown format so you can easily paste it into:
	•	Notion
	•	Obsidian
	•	HackMD
	•	VSCode + Marp
	•	Pandoc
	•	PowerPoint AI generators
	•	Google Slides import

You can also convert this directly into slides using Marp or Pandoc.

⸻

Moat Policy Dimension Orchestrator

Managing Multi-Dimensional Policy Evaluation

Author: Vivek Jain
Year: 2026

⸻

Problem Statement

Modern data platforms have many policy types.

Examples:

• Regulatory compliance
• Data classification (PII, PCI, PHI)
• Geography restrictions
• Role based access
• Resource specific policies
• Runtime context checks

Problem

Policies often conflict with each other.

Example:

Role policy → Allow
Geography policy → Deny

Which one wins?

We need:

• deterministic ordering
• governance control
• explainable decisions

⸻

Core Idea

Policies should not rely on file order.

Instead we introduce:

Policy Dimensions

Each policy belongs to a dimension.

Each dimension defines:

• Priority
• Effect (allow / deny / constraint)
• Combination strategy
• Override capability

This creates structured policy orchestration.

⸻

Example Policy Dimensions
	1.	Emergency Security
	2.	Regulatory Compliance
	3.	Data Classification
	4.	Geography / Residency
	5.	Role Entitlements
	6.	Resource Policies
	7.	Runtime Context
	8.	Approved Exceptions

Each dimension evaluates independently.

A decision composer merges the results.

⸻

Recommended Policy Precedence

Enterprise safe ordering:

L0  Emergency Security
L1  Regulatory Compliance
L2  Tenant / Domain Boundary
L3  Data Classification
L4  Geography / Residency
L5  Runtime Context
L6  Role / ABAC Entitlements
L7  Resource Policy
L8  Masking / Row Filtering
L9  Approved Exception
L10 Default Deny

Key rule:

Higher layers override lower layers.

Example:

Regulatory deny cannot be overridden.

⸻

Architecture Overview

Authorization pipeline:

Request
   ↓
Context Builder
   ↓
Dimension Evaluators
   ↓
Policy Precedence Registry
   ↓
Decision Composer
   ↓
Final Decision + Explainability


⸻

Context Builder

Build request context:

User Identity
Roles / Groups
Resource Metadata
Dataset Classification
Geography
Runtime Context

Example:

{
 user: "analyst1",
 role: ["data_analyst"],
 dataset: "customer_table",
 classification: "PII",
 geography: "EU",
 time: "business_hours"
}


⸻

Dimension Evaluators

Each dimension runs independent policies.

Example outputs:

Geography Policy

{
 dimension: "geography",
 decision: "deny",
 reason: "dataset restricted to EU"
}

Role Policy

{
 dimension: "role",
 decision: "allow",
 reason: "user has analyst role"
}

Classification Policy

{
 dimension: "classification",
 decision: "allow",
 constraints: ["mask_ssn"]
}


⸻

Policy Precedence Registry

Central governance configuration.

Example:

dimensions:

  regulatory:
    priority: 900
    combiner: deny_overrides

  classification:
    priority: 800
    combiner: most_restrictive

  geography:
    priority: 700
    combiner: deny_overrides

  role:
    priority: 600
    combiner: union_allows

Benefits:

• Admin controlled ordering
• No policy code changes required
• Governance friendly

⸻

Decision Composition Logic

Evaluation algorithm:

1 Evaluate all dimensions
2 Check hard deny layers
3 Aggregate allow decisions
4 Merge constraints
5 Apply approved exceptions
6 Produce final decision

Pseudo logic:

if hard_deny:
   result = deny
else if allow:
   result = allow_with_constraints
else:
   result = deny


⸻

Example Final Decision

{
 final_decision: "allow",
 winning_dimension: "classification",

 base_allow: ["role_entitlement"],

 applied_constraints:
   - column_mask(ssn)
   - row_filter(region='EU'),

 audit_trace:
   - role policy allowed
   - classification policy applied masking
   - geography policy checked
}


⸻

Explainable Authorization

Instead of returning only:

true / false

The system returns:

• final decision
• winning policy dimension
• applied constraints
• evaluation trace
• policy identifiers
• audit metadata

This is critical for enterprise governance.

⸻

Benefits

Governance

Clear separation of policy domains.

Deterministic Behavior

No random rule ordering.

Human Control

Admins control policy precedence.

Explainability

Decisions are auditable.

Scalability

Multiple teams can write policies without conflicts.

Compatibility

Works naturally with:

• Moat
• OPA
• Trino
• OpenMetadata
• Data Mesh architectures

⸻

One-Line Executive Summary

Moat evaluates policies by dimension instead of rule order, using a central precedence registry to control which policy domains win and how conflicts are resolved.

⸻

If you want, I can also give you a much stronger version used by big tech companies:

“Policy Dimension Architecture used by Netflix, Google, and Airbnb”

with:
	•	policy stack diagram
	•	real policy conflict scenarios
	•	enterprise governance model
	•	Moat + OPA + Trino architecture

That version becomes a 20-slide architecture deck perfect for VP / Distinguished Engineer reviews.