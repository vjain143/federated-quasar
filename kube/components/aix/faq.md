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
