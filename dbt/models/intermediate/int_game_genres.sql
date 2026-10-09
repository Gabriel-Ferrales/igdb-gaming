/*
Model: int_game_genres

Purpose:
Resolve the many-to-many relationship between games and genres.

Grain:
One row per game_id + genre_id.

Business key:
game_id + genre_id.

Inputs:
- stg_games

Future use:
- bridge_game_genres
- genre analysis marts
*/

with exploded_genres as (

    select
        games.game_id,
        genre_id
    from {{ ref('stg_games') }} as games
    cross join unnest(games.genres) as genre_id

),

final as (

    select distinct
        game_id,
        genre_id
    from exploded_genres
    where game_id is not null
      and genre_id is not null

)

select * from final
