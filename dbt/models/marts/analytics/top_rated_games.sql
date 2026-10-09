/*
Model: top_rated_games

Purpose:
Expose game-level current rating measures for flexible ranking and filtering in
BI tools.

Grain:
One row per game_id.

Metric behavior:
No minimum rating-count threshold is applied. Consumers can use rating_count
and aggregated_rating_count to select an appropriate confidence threshold.
Ratings represent the current loaded state and are not historical snapshots.
*/

select
    games.game_id,
    games.name as game_name,
    date(games.first_release_date_ts) as first_release_date,
    ratings.rating as user_rating,
    ratings.rating_count as user_rating_count,
    ratings.aggregated_rating,
    ratings.aggregated_rating_count,
    ratings.snapshot_date as rating_snapshot_date
from {{ ref('dim_games') }} as games
inner join {{ ref('fct_game_ratings') }} as ratings
    on games.game_id = ratings.game_id
