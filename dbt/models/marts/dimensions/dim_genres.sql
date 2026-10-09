/*
Model: dim_genres

Purpose:
Provide the current descriptive attributes of each IGDB genre.

Grain:
One row per genre_id.

Primary key:
genre_id.

Foreign keys:
None.

Inputs:
- stg_genres
*/

with ranked_genres as (

    select
        genre_id,
        name,
        slug,
        created_at,
        created_at_ts,
        updated_at,
        updated_at_ts,
        row_number() over (
            partition by genre_id
            order by updated_at desc, _loaded_at desc
        ) as row_number
    from {{ ref('stg_genres') }}
    where genre_id is not null

)

select
    genre_id,
    name,
    slug,
    created_at,
    created_at_ts,
    updated_at,
    updated_at_ts
from ranked_genres
where row_number = 1
