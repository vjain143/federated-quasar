# FAQ

## Do I need the OPA binary in an independent Moat pod?

Yes, if that pod is responsible for generating Moat bundles, it needs the `opa`
binary.

Moat does not run OPA as its policy decision engine, but it does invoke the OPA
CLI to build bundles. The bundle generator shells out to `opa build`, and the
worker uses that code path when it refreshes bundles. In practice:

- If the pod runs the worker or generates bundles, install the `opa` binary.
- If the pod is API-only and only serves bundles that were built elsewhere, the
  `opa` binary is not strictly required.
- The runtime OPA server that evaluates policies for Trino should still be
  deployed separately, ideally close to the Trino coordinator.

## Is Trino using `rules.json` or OPA in this repo?

OPA.

The active Trino configuration is:

- [access-control.properties](/Users/vivek/Lab/GitHub/federated-quasar/kube/components/fq/trino/configs/access-control.properties)

That file sets:

- `access-control.name=opa`

So Trino calls OPA for authorization decisions. The mounted `rules.json` file is
not the active authorization source in the current setup.

## Does the current `fq` Trino stack use a Trino file group provider?

No.

There is no `group-provider.properties` or equivalent group provider config in:

- [configs](/Users/vivek/Lab/GitHub/federated-quasar/kube/components/fq/trino/configs)

That means Trino is not currently loading group membership from a local file in
this stack.

## If Trino uses OPA, where should group-based rules live?

In the OPA bundle, not in Trino's file rules.

The intended design is:

1. Moat stores users, groups, and policy inputs.
2. Moat builds a policy bundle.
3. OPA downloads that bundle.
4. Trino calls OPA for `allow`, `rowFilters`, and `columnMask`.

In that architecture, group membership and rule evaluation should be encoded in
Rego and bundle data served through OPA.

## What is Moat used for if Trino talks directly to OPA?

Moat is the policy management layer, not the runtime decision engine.

It is responsible for:

- managing identity and group metadata
- storing policy-related application data
- generating policy bundles
- serving those bundles to OPA

OPA is the runtime decision point that Trino queries directly.

## Can I still use Trino `rules.json` with Moat?

Not as the active path in the current repo configuration.

You have two distinct models:

- `OPA model`: Trino uses the OPA plugin, and rules live in Rego plus OPA data.
- `File model`: Trino uses file-based access control and optional file-based
  group mapping.

This repo is currently wired for the `OPA model`.

If you want the `File model`, you would need to explicitly switch Trino away
from OPA and implement a separate process that exports Moat-managed data into
Trino-compatible files.

## What happens if I use Trino file-based ACL with logical groups and comma-separated members?

If you switch Trino to the file-based ACL model, then Trino will evaluate those
files directly and use them as the source of truth.

That means:

- the group mapping file defines logical group names
- each group maps to a comma-separated list of Trino usernames
- `rules.json` is evaluated against those group names

For example, if your group mapping file says:

```text
analysts=alice,bob,charlie
```

Then Trino interprets that as:

- group name: `analysts`
- members: `alice`, `bob`, `charlie`

If `rules.json` contains rules for `analysts`, those rules apply to any Trino
request made by `alice`, `bob`, or `charlie` after authentication.

Important boundary:

- those groups exist only inside Trino's local file configuration
- Moat does not automatically read them
- OPA does not automatically evaluate them
- there is no built-in sync in this repo from Trino file groups into Moat or OPA

So if you use file-based ACL, Trino can enforce those logical groups locally,
but that does not make them part of the Moat-managed policy model unless you
explicitly build a sync/export path.

## What happens if both Trino file ACL files and OPA config exist at the same time?

The active Trino access-control plugin decides which path is used.

If Trino is configured with:

- `access-control.name=opa`

then OPA is the active authorization engine, and the local file-based ACL data
is not the active policy source.

If Trino is configured for the file-based plugin instead, then Trino evaluates:

- the file-based group mapping
- `rules.json`

and OPA is no longer the active authorization engine for those decisions.

The main risk is configuration drift:

- local Trino file groups can diverge from Moat groups
- `rules.json` can diverge from Rego policy
- operators may think both are enforced when only one path is actually active

To avoid that, keep a single source of truth:

- use the `OPA model` if Moat should own users, groups, and policy inputs
- use the `File model` if Trino local files should own groups and access rules

## How do I define groups in Moat?

Use the SCIM endpoints exposed by Moat.

Relevant routes:

- `/api/scim/v2/Users`
- `/api/scim/v2/Groups`

In the current local dev setup, `api.scim.auth_method: none` is configured, so
those endpoints can be called without auth.

Example:

```bash
curl -s http://localhost:32080/api/scim/v2/Groups
curl -s http://localhost:32080/api/scim/v2/Users
```

## If I provide AD groups, can Moat pull members from LDAP or a REST API and store them?

Partially, yes.

This repo already supports two ingestion patterns for identity data:

- `LDAP connector`: pulls users from LDAP and reads group membership from an
  attribute such as `memberOf`
- `HTTP connector`: pulls users and attributes from a JSON REST API

What the current implementation does today:

- it ingests users into Moat principals
- it stores group membership as principal attributes, typically with the key
  `ad_group`
- OPA bundle generation can then use those principal attributes as policy input

What it does not do automatically today:

- it does not automatically convert LDAP or HTTP group membership into
  `principal_groups` records with a stored `members` list
- it does not provide a built-in sync job that says "take this set of AD groups,
  fetch all members, and materialize them as Moat group objects"

So, if LDAP returns that `alice` belongs to `finance_readers`, Moat can store
that as:

- principal: `alice`
- attribute: `ad_group=finance_readers`

That is enough if your Rego policy checks principal attributes.

If you want first-class Moat groups with explicit member lists, use one of these
paths:

1. create and update groups through Moat's SCIM Groups API
2. add a custom ingestion step that transforms LDAP or HTTP membership data into
   `principal_groups`

The most practical short-term model is:

- ingest AD membership as `ad_group` principal attributes
- write Rego against `ad_group`

The more complete long-term model is:

- materialize those memberships into Moat group objects
- use `principal_groups` as the authoritative group store

## Why does the sample `policy.rego` not use groups?

Because it is only a placeholder.

The sample policy currently just allows one operation:

- [policy.rego](/Users/vivek/Lab/GitHub/federated-quasar/kube/components/aix/kubernetes/moat/configs/policy.rego)

It is enough to prove the plumbing, but not enough to implement real
authorization. You still need to extend it with:

- identity inputs
- group membership data
- object-level rules
- row filters
- column masks

## What should I build next to get real group-based Trino authorization?

The next practical steps are:

1. Define users and groups in Moat through SCIM.
2. Extend Moat's bundle generation to include group membership and policy data.
3. Replace the placeholder Rego with group-aware Rego rules.
4. Validate Trino requests against OPA using real user/group inputs.

## How do I verify the cross-namespace Trino -> OPA path?

From the Trino coordinator pod:

```bash
kubectl exec -n fq deploy/fq-trino-coordinator -- getent hosts opa.aix.svc.cluster.local
kubectl exec -n fq deploy/fq-trino-coordinator -- curl -sS http://opa.aix.svc.cluster.local:8181/v1/data/trino/allow
```

Expected:

- DNS resolution succeeds
- OPA returns JSON such as `{"result":false}`

## Can I use dbt with Trino and then feed metadata to Moat through OpenMetadata?

Yes. A working pattern is:

1. Run dbt against Trino to materialize tables.
2. Ingest Trino metadata into OpenMetadata (database service + schema + tables).
3. Ingest dbt artifacts (`manifest.json`, `catalog.json`, `run_results.json`)
   into OpenMetadata for model-level context.
4. Pull OpenMetadata attributes/tags into Moat resource attributes and enforce
   them in OPA policy.

In this repo, the ready-to-use files are:

- dbt project:
  - [kube/components/fq/dbt](/Users/vivek/Lab/GitHub/federated-quasar/kube/components/fq/dbt)
- OpenMetadata workflows:
  - [trino-metadata.yaml](/Users/vivek/Lab/GitHub/federated-quasar/kube/components/om/workflows/fq/trino-metadata.yaml)
  - [dbt-metadata.yaml](/Users/vivek/Lab/GitHub/federated-quasar/kube/components/om/workflows/fq/dbt-metadata.yaml)

Important: with OPA auth enabled in Trino, policy responses must match Trino's
expected shape. If optional endpoints like `columnMask` are configured, the
returned object must be valid for Trino or requests can fail with deserialization
errors.
