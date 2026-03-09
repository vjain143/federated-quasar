{{ config(materialized='table') }}

select
  1 as order_id,
  'enterprise' as business_domain,
  'confidential' as sensitivity_tier,
  current_timestamp as created_at
