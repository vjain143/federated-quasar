package trino.domain

import rego.v1

# Default deny for domain-restricted data
default allow := false

# Helper functions
is_enterprise_user if {
  some i in input.context.identity.groups
  i == "enterprise_users"
}

is_finance_domain_user if {
  some i in input.context.identity.groups
  i == "finance_domain"
}

is_admin if {
  some i in input.context.identity.groups
  i == "admin"
}

# Domain-based access rules
allow if {
  # Public domain data is accessible to all
  is_public_domain
}

allow if {
  # Enterprise domain requires enterprise user access
  is_enterprise_domain
  is_enterprise_user
}

allow if {
  # Finance domain requires finance domain access
  is_finance_domain
  is_finance_domain_user
}

allow if {
  # Admins can access all domains
  is_admin
}

# Helper functions to determine domain
is_public_domain if {
  resource_tags := get_resource_tags
  some tag in resource_tags
  contains(tag.tagFQN, "domain:public")
}

is_enterprise_domain if {
  resource_tags := get_resource_tags
  some tag in resource_tags
  contains(tag.tagFQN, "domain:enterprise")
}

is_finance_domain if {
  resource_tags := get_resource_tags
  some tag in resource_tags
  contains(tag.tagFQN, "domain:finance")
}

# Extract tags from resource attributes
get_resource_tags := [tag | tag := data.resource_attributes[input.action.resource.name].tags[_]]
