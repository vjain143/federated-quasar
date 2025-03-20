package trino.authz

default allow = false  # Deny everything by default

allow {
    input.method == "POST"                      # Only allow POST (query execution)
    input.user == "admin"                        # Allow admin user full access
}

allow {
    input.user == "analyst"
    input.query contains "SELECT"               # Analysts can only SELECT
    not input.query contains "DELETE"           # No DELETE access
}