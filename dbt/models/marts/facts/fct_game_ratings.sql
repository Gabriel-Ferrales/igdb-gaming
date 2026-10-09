/*
Model: fct_game_ratings

Purpose:
Provide the current rating metrics available for each IGDB game.

Grain:
One row per game_id representing the current loaded rating state.

Primary key:
game_id.

Foreign keys:
- game_id -> dim_games.game_id

Inputs:
- stg_games

Important metric behavior:
This model does not preserve real history. Each execution replaces the prior
state because it is materialized as a table. snapshot_date records the build
date only; it does not make the model a historical snapshot.
*/

with ranked_ratings as (

    select
        game_id,
        rating,
        rating_count,
        aggregated_rating,
        aggregated_rating_count,
        row_number() over (
            partition by game_id
            order by updated_at desc, _loaded_at desc
        ) as row_number
    from {{ ref('stg_games') }}
    where game_id is not null

)

select
    game_id,
    rating,
    rating_count,
    aggregated_rating,
    aggregated_rating_count,
    current_date() as snapshot_date
from ranked_ratings
where row_number = 1
