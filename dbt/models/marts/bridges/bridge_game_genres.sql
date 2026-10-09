/*
Model: bridge_game_genres

Purpose:
Connect games with their associated genres.

Grain:
One row per game_id + genre_id.

Business key:
game_id + genre_id.

Foreign keys:
- game_id -> dim_games.game_id
- genre_id -> dim_genres.genre_id

Inputs:
- int_game_genres
*/

select
    game_id,
    genre_id
from {{ ref('int_game_genres') }}
