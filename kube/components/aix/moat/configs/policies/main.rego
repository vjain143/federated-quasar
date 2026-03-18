package trino

import rego.v1

# Default deny - explicit allow required
default allow := false
default rowFilters := []
default columnMask := null

# Import policy dimensions
classification_allow := data.trino.classification.allow
domain_allow := data.trino.domain.allow  
access_allow := data.trino.access.allow

# Service principals used by platform automation
trusted_service_principals := {"dbt", "openmetadata"}

identity := object.get(object.get(input, "context", {}), "identity", {})
user_name := lower(object.get(identity, "user", ""))

# Allow trusted automation users to run platform-managed operations.
allow if {
  trusted_service_principals[user_name]
}

# Main decision logic - all dimensions must allow
allow if {
  # All policy dimensions must grant access
  classification_allow
  domain_allow
  access_allow
}

# Combine row filters from all dimensions
access_row_filters := object.get(data.trino.access, "row_filters", [])
classification_row_filters := object.get(data.trino.classification, "row_filters", [])
row_filters := array.concat(access_row_filters, classification_row_filters)

# Combine column masks from all dimensions
classification_column_mask := object.get(data.trino.classification, "column_mask", {})
access_column_mask := object.get(data.trino.access, "column_mask", {})
column_mask := object.union(classification_column_mask, access_column_mask)

# Apply combined filters
rowFilters := row_filters if {
  count(row_filters) > 0
}

# Apply combined column masks
columnMask := column_mask if {
  count(column_mask) > 0
}

# Audit logging
decision := {
  "allow": allow,
  "reason": get_reason,
  "applied_policies": [
    "classification",
    "domain", 
    "access"
  ],
  "row_filters": rowFilters,
  "column_mask": columnMask
}

get_reason := "granted" if {
  allow
}

get_reason := "denied" if {
  not allow
}
