/*
Model: int_game_platforms

Purpose:
Resolve the many-to-many relationship between games and platforms.

Grain:
One row per game_id + platform_id.

Business key:
game_id + platform_id.

Inputs:
- stg_games

Future use:
- bridge_game_platforms
*/

with exploded_platforms as (

    select
        games.game_id,
        platform_id
    from {{ ref('stg_games') }} as games
    cross join unnest(games.platforms) as platform_id

)

select distinct
    game_id,
    platform_id
from exploded_platforms
where game_id is not null
  and platform_id is not null
