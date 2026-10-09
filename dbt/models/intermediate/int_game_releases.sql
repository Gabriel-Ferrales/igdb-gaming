/*
Model: int_game_releases

Purpose:
Prepare individual game release events.

Grain:
One row per release_date_id.

Business key:
release_date_id.

Inputs:
- stg_release_dates

Future use:
- fct_game_releases
- platform and release-date marts
*/

with releases as (

    select
        release_dates.release_date_id,
        release_dates.game_id,
        release_dates.platform_id,
        release_dates.release_date_raw,
        release_dates.release_timestamp,
        release_dates.release_date,
        release_dates.region,
        release_dates.category as release_category,
        release_dates.updated_at,
        release_dates._loaded_at
    from {{ ref('stg_release_dates') }} as release_dates
    inner join {{ ref('stg_games') }} as games
        on release_dates.game_id = games.game_id

),

deduplicated as (

    select
        release_date_id,
        game_id,
        platform_id,
        release_date_raw,
        release_timestamp,
        release_date,
        region,
        release_category,
        row_number() over (
            partition by release_date_id
            order by updated_at desc, _loaded_at desc
        ) as row_number
    from releases
    where release_date_id is not null
      and game_id is not null

)

select
    release_date_id,
    game_id,
    platform_id,
    release_date_raw,
    release_timestamp,
    release_date,
    region,
    release_category
from deduplicated
where row_number = 1
