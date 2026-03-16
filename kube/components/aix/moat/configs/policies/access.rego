package trino.access

import rego.v1

# Default deny for access-controlled operations
default allow := false

# Define allowed operations by access level
reader_operations := {
  "AccessCatalog",
  "FilterCatalogs", 
  "FilterColumns",
  "FilterSchemas",
  "FilterTables",
  "SelectFromColumns",
  "ShowSchemas",
  "ShowTables",
  "ExecuteQuery"
}

writer_operations := {
  "AccessCatalog",
  "CreateSchema",
  "CreateTable", 
  "InsertIntoTable",
  "DeleteFromTable",
  "DropSchema",
  "DropTable",
  "RenameSchema",
  "RenameTable",
  "ExecuteQuery"
}

# Helper functions
has_finance_reader_access if {
  some i in input.context.identity.groups
  i == "finance_reader"
}

has_finance_writer_access if {
  some i in input.context.identity.groups
  i == "finance_writer"
}

is_admin if {
  some i in input.context.identity.groups
  i == "admin"
}

# Access control rules
allow if {
  # Finance reader can perform read operations
  requires_finance_reader_access
  has_finance_reader_access
  input.action.operation in reader_operations
}

allow if {
  # Finance writer can perform both read and write operations
  requires_finance_writer_access
  has_finance_writer_access
  input.action.operation in writer_operations
}

allow if {
  # Admins can perform any operation
  is_admin
}

# Helper functions to determine required access level
requires_finance_reader_access if {
  resource_tags := get_resource_tags()
  some tag in resource_tags
  contains(tag.tagFQN, "access:finance_reader")
}

requires_finance_writer_access if {
  resource_tags := get_resource_tags()
  some tag in resource_tags
  contains(tag.tagFQN, "access:finance_writer")
}

# Extract tags from resource attributes
get_resource_tags := [tag | tag := data.resource_attributes[input.action.resource.name].tags[_]]

# Row filtering for finance readers
row_filters := [{"column": "department", "operator": "=", "value": "finance"}] if {
  requires_finance_reader_access
  has_finance_reader_access
  not is_admin
}
