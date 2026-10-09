/*
Model: bridge_game_platforms

Purpose:
Connect games with their associated platforms.

Grain:
One row per game_id + platform_id.

Business key:
game_id + platform_id.

Foreign keys:
- game_id -> dim_games.game_id
- platform_id -> dim_platforms.platform_id

Inputs:
- int_game_platforms
*/

select
    game_id,
    platform_id
from {{ ref('int_game_platforms') }}
