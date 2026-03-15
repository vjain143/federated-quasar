{{ config(
    materialized='table',
    alias='fq_orders_summary',
    tags=[
      'domain:enterprise',
      'classification:confidential',
      'access:finance_reader'
    ],
    meta={
      'data_domain': 'enterprise',
      'data_owner_team': 'finance-analytics',
      'data_classification': 'confidential',
      'contains_pii': false,
      'retention': 'P90D',
      'access_policy': {
        'read_roles': ['finance_reader'],
        'purpose': 'summary reporting'
      }
    }
) }}

select
    'enterprise' as business_domain,
    'confidential' as sensitivity_tier,
    1 as total_orders,
    current_timestamp as last_created_at
