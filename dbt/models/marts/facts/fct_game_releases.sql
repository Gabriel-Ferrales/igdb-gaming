/*
Model: fct_game_releases

Purpose:
Represent individual IGDB game release events.

Grain:
One row per release_date_id.

Primary key:
release_date_id.

Foreign keys:
- game_id -> dim_games.game_id
- platform_id -> dim_platforms.platform_id

Inputs:
- int_game_releases

Important metric behavior:
release_count is always 1 and is additive across release event rows.
release_date is a calendar DATE derived from the safely converted source
timestamp. Null source dates remain null. The raw Unix value and UTC timestamp
are retained for lineage and debugging.
*/

select
    release_date_id,
    game_id,
    platform_id,
    release_date_raw,
    release_timestamp,
    release_date,
    region,
    release_category,
    1 as release_count
from {{ ref('int_game_releases') }}
