/*
Model: dim_platforms

Purpose:
Provide the current descriptive and analytical attributes of each IGDB platform.

Grain:
One row per platform_id.

Primary key:
platform_id.

Foreign keys:
- platform_family references an IGDB platform family identifier.
- platform_logo references an IGDB platform logo identifier.

Inputs:
- stg_platforms
*/

with ranked_platforms as (

    select
        platform_id,
        name,
        slug,
        abbreviation,
        alternative_name,
        category,
        generation,
        platform_family,
        platform_logo,
        created_at,
        created_at_ts,
        updated_at,
        updated_at_ts,
        row_number() over (
            partition by platform_id
            order by updated_at desc, _loaded_at desc
        ) as row_number
    from {{ ref('stg_platforms') }}
    where platform_id is not null

)

select
    platform_id,
    name,
    slug,
    abbreviation,
    alternative_name,
    category,
    generation,
    platform_family,
    platform_logo,
    created_at,
    created_at_ts,
    updated_at,
    updated_at_ts
from ranked_platforms
where row_number = 1
