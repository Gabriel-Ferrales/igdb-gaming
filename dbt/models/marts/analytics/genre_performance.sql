/*
Model: genre_performance

Purpose:
Summarize current game coverage and rating performance by genre.

Grain:
One row per genre_id.

Metric behavior:
A multi-genre game contributes once to each assigned genre. Ratings represent
the current loaded state, not historical observations. No release or platform
relationship is joined, avoiding independent many-to-many fanout.
*/

with genre_metrics as (

    select
        game_genres.genre_id,
        count(distinct game_genres.game_id) as distinct_game_count,
        count(distinct if(ratings.rating is not null, game_genres.game_id, null))
            as games_with_user_rating,
        avg(ratings.rating) as average_user_rating,
        coalesce(sum(ratings.rating_count), 0) as total_user_rating_count,
        count(distinct if(ratings.aggregated_rating is not null, game_genres.game_id, null))
            as games_with_critic_rating,
        avg(ratings.aggregated_rating) as average_aggregated_rating
    from {{ ref('bridge_game_genres') }} as game_genres
    left join {{ ref('fct_game_ratings') }} as ratings
        on game_genres.game_id = ratings.game_id
    group by game_genres.genre_id

)

select
    genres.genre_id,
    genres.name as genre_name,
    coalesce(metrics.distinct_game_count, 0) as distinct_game_count,
    coalesce(metrics.games_with_user_rating, 0) as games_with_user_rating,
    metrics.average_user_rating,
    coalesce(metrics.total_user_rating_count, 0) as total_user_rating_count,
    coalesce(metrics.games_with_critic_rating, 0) as games_with_critic_rating,
    metrics.average_aggregated_rating
from {{ ref('dim_genres') }} as genres
left join genre_metrics as metrics
    on genres.genre_id = metrics.genre_id
