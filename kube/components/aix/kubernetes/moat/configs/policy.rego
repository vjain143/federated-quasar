package trino

import rego.v1

default allow := false
default rowFilters := []
default columnMask := null

dbt_allowed_ops := {
  "AccessCatalog",
  "CreateSchema",
  "CreateTable",
  "DeleteFromTable",
  "DropSchema",
  "DropTable",
  "ExecuteQuery",
  "FilterCatalogs",
  "FilterColumns",
  "FilterSchemas",
  "FilterTables",
  "InsertIntoTable",
  "RenameSchema",
  "RenameTable",
  "SelectFromColumns",
  "ShowSchemas",
  "ShowTables"
}

openmetadata_allowed_ops := {
  "AccessCatalog",
  "FilterCatalogs",
  "FilterColumns",
  "FilterSchemas",
  "FilterTables",
  "SelectFromColumns",
  "ShowSchemas",
  "ShowTables"
}

protected_catalog := "hms_db"
protected_schema := "fq_dbt"
protected_table := "fq_orders"
required_group := "rwx"

identity := object.get(object.get(input, "context", {}), "identity", {})
resource := object.get(object.get(input, "action", {}), "resource", {})

is_required_group_member if {
  some group in object.get(identity, "groups", [])
  group == required_group
}

is_protected_table if {
  table := object.get(resource, "table", null)
  table != null
  table.catalogName == protected_catalog
  table.schemaName == protected_schema
  table.tableName == protected_table
}

is_protected_table if {
  column := object.get(resource, "column", null)
  column != null
  column.catalogName == protected_catalog
  column.schemaName == protected_schema
  column.tableName == protected_table
}

# Keep current permissive behavior for all other resources.
allow if {
  not is_protected_table
}

# Restrict hms_db.fq_dbt.fq_orders to rwx group members only.
allow if {
  is_protected_table
  is_required_group_member
}
