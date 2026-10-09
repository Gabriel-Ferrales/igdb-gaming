/*
Model: games_release_trends

Purpose:
Provide yearly release activity for BI trend analysis.

Grain:
One row per non-null release_year.

Metric behavior:
- release_count counts release event rows, including separate platform, region,
  or category records for the same game.
- distinct_games_released counts each game once within a year.
- distinct_platforms counts non-null platforms with a release event that year.
*/

select
    extract(year from release_date) as release_year,
    count(*) as release_count,
    count(distinct game_id) as distinct_games_released,
    count(distinct platform_id) as distinct_platforms
from {{ ref('fct_game_releases') }}
where release_date is not null
group by release_year
