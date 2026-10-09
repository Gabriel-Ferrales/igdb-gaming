/*
Model: dim_companies

Purpose:
Provide the current descriptive and analytical attributes of each IGDB company.

Grain:
One row per company_id.

Primary key:
company_id.

Foreign keys:
- parent references an IGDB company identifier.
- changed_company_id references the successor IGDB company identifier.
- logo references an IGDB company logo identifier.

Inputs:
- stg_companies
*/

with ranked_companies as (

    select
        company_id,
        name,
        slug,
        description,
        country,
        parent,
        start_date,
        start_date_ts,
        changed_company_id,
        logo,
        url,
        created_at,
        created_at_ts,
        updated_at,
        updated_at_ts,
        row_number() over (
            partition by company_id
            order by updated_at desc, _loaded_at desc
        ) as row_number
    from {{ ref('stg_companies') }}
    where company_id is not null

)

select
    company_id,
    name,
    slug,
    description,
    country,
    parent,
    start_date,
    start_date_ts,
    changed_company_id,
    logo,
    url,
    created_at,
    created_at_ts,
    updated_at,
    updated_at_ts
from ranked_companies
where row_number = 1
