/*
Model: dim_games

Purpose:
Provide the current descriptive and analytical attributes of each IGDB game.

Grain:
One row per game_id.

Primary key:
game_id.

Foreign keys:
None.

Inputs:
- stg_games
*/

with ranked_games as (

    select
        game_id,
        name,
        slug,
        summary,
        category,
        status,
        first_release_date,
        first_release_date_ts,
        created_at,
        created_at_ts,
        updated_at,
        updated_at_ts,
        row_number() over (
            partition by game_id
            order by updated_at desc, _loaded_at desc
        ) as row_number
    from {{ ref('stg_games') }}
    where game_id is not null

)

select
    game_id,
    name,
    slug,
    summary,
    category,
    status,
    first_release_date,
    first_release_date_ts,
    created_at,
    created_at_ts,
    updated_at,
    updated_at_ts
from ranked_games
where row_number = 1
