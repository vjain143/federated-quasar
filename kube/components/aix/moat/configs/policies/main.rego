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

# Main decision logic - all dimensions must allow
allow if {
  # All policy dimensions must grant access
  classification_allow
  domain_allow
  access_allow
}

# Combine row filters from all dimensions
row_filters := array.concat([
  data.trino.access.rowFilters,
  data.trino.classification.rowFilters
])

# Combine column masks from all dimensions
column_mask := object.union(
  data.trino.classification.column_mask,
  {}
)

# Helper function to combine arrays
array_concat(arrays) = result if {
  count(arrays) > 0
  result := arrays[_][_]  # Flatten nested arrays
}

# Fallback for empty arrays
array_concat(arrays) = [] if {
  count(arrays) == 0
}

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
  "reason": get_reason(),
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
