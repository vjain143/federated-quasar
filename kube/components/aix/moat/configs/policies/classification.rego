package trino.classification

import rego.v1

# Default deny for confidential data
default allow := false

# Helper functions
has_confidential_access if {
  some i in input.context.identity.groups
  i == "confidential_access"
}

is_finance_team if {
  some i in input.context.identity.groups
  i == "finance_team"
}

is_data_steward if {
  some i in input.context.identity.groups
  i == "data_steward"
}

# Classification-based rules
allow if {
  # Non-confidential data is accessible to all authenticated users
  not is_confidential_data
}

allow if {
  # Confidential data requires special access
  is_confidential_data
  has_confidential_access
}

allow if {
  # Finance team can access confidential finance data
  is_confidential_data
  is_finance_team
}

allow if {
  # Data stewards can access all confidential data
  is_confidential_data
  is_data_steward
}

# Helper to determine if data is confidential
is_confidential_data if {
  resource_tags := get_resource_tags
  some tag in resource_tags
  contains(tag.tagFQN, "classification:confidential")
}

# Extract tags from resource attributes
get_resource_tags := [tag | tag := data.resource_attributes[input.action.resource.name].tags[_]]

# Column masking for confidential data
column_mask := {"ssn": "MASKED", "email": "MASKED"} if {
  is_confidential_data
  not has_confidential_access
  not is_finance_team
  not is_data_steward
}
