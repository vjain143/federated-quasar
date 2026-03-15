{{ config(
    materialized='table',
    alias='fq_orders_as_select2',
    tags=[
      'domain:enterprise',
      'classification:confidential',
      'access:finance_reader',
      'access:finance_writer'
    ],
    meta={
      'data_domain': 'enterprise',
      'data_owner_team': 'finance-analytics',
      'data_classification': 'confidential',
      'contains_pii': false,
      'retention': 'P90D',
      'access_policy': {
        'read_roles': ['finance_reader'],
        'write_roles': ['finance_writer'],
        'purpose': 'finance reporting'
      }
    }
) }}

select
  1 as order_id,
  'enterprise' as business_domain,
  'confidential' as sensitivity_tier,
  current_timestamp as created_at
