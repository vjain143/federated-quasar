  package nessie.authz
    
    default allow = false
    
    allow {
    input.query == "SELECT * FROM sensitive_table"
    input.user == "admin"
  }