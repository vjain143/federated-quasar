package trino

import rego.v1

default allow := false

allow if {
  input.action.operation == "SelectFromColumns"
}
