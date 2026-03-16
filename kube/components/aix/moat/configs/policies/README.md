# MOAT Policies for dbt Tag-Based Governance

## Policy Structure

This policy suite implements multi-dimensional access control based on dbt tags:

### Policy Dimensions

1. **Classification Policy** (`classification.rego`)
   - Controls access based on data sensitivity (confidential, public, etc.)
   - Applies column masking for sensitive data
   - Requires special groups for confidential data access

2. **Domain Policy** (`domain.rego`)
   - Controls access based on data domain (enterprise, finance, public, etc.)
   - Maps domains to user groups
   - Provides domain-specific access rules

3. **Access Policy** (`access.rego`)
   - Controls operations based on access level (reader, writer)
   - Maps operations to permissions
   - Applies row filtering where appropriate

4. **Main Orchestrator** (`main.rego`)
   - Combines all policy dimensions
   - Ensures all dimensions must allow access
   - Combines row filters and column masks

## Required User Groups

For the policies to work, users must be in these groups:

### Classification Groups
- `confidential_access` - Can access confidential data
- `finance_team` - Finance team members
- `data_steward` - Data stewards with broad access

### Domain Groups  
- `enterprise_users` - Enterprise domain users
- `finance_domain` - Finance domain users
- `admin` - System administrators

### Access Groups
- `finance_reader` - Read-only access to finance data
- `finance_writer` - Read/write access to finance data

## Example Access Scenarios

### Finance Writer accessing fq_orders_as_select
- **Tags**: domain:enterprise, classification:confidential, access:finance_reader, access:finance_writer
- **Required Groups**: enterprise_users, finance_writer, confidential_access OR finance_team
- **Allowed Operations**: All writer_operations (SELECT, INSERT, UPDATE, DELETE)

### Finance Reader accessing fq_orders_as_select  
- **Tags**: domain:enterprise, classification:confidential, access:finance_reader
- **Required Groups**: enterprise_users, finance_reader, confidential_access OR finance_team
- **Allowed Operations**: reader_operations only (SELECT, SHOW)
- **Row Filters**: May apply department=finance filter

## Deployment

1. Update MOAT kustomization to include policies directory
2. Restart MOAT to load new policies
3. Verify OPA bundle generation includes all policies
4. Test with sample requests

## Testing

Use `test-data.json` for unit testing policies with OPA test framework.
