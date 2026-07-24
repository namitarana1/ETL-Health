-- Gold-layer Snowflake models. PHI identifiers are intentionally absent.
create or replace view analytics.provider_claim_kpis as
select
  provider_id,
  count(*) as claim_count,
  count_if(status = 'APPROVED') / nullif(count(*), 0) as approval_rate,
  count_if(status = 'DENIED') / nullif(count(*), 0) as denial_rate,
  sum(allowed_amount) as allowed_amount,
  sum(paid_amount) as paid_amount,
  sum(allowed_amount - paid_amount) as payment_variance
from curated.claims
group by provider_id;

create or replace view analytics.authorization_turnaround as
select
  date_trunc('month', requested_at) as month,
  avg(datediff('hour', requested_at, decision_at)) as avg_turnaround_hours,
  count_if(decision = 'DENIED') as denied_authorizations
from curated.authorizations
group by 1;
