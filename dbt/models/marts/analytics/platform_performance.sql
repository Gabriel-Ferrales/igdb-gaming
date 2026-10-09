/*
Model: platform_performance

Purpose:
Summarize game catalog coverage and release activity by platform.

Grain:
One row per platform_id.

Metric behavior:
Catalog game counts and release-event measures are aggregated independently at
platform grain before they are joined. This prevents multiplying release rows
by game-platform bridge rows.
*/

with platform_games as (

    select
        platform_id,
        count(distinct game_id) as distinct_game_count
    from {{ ref('bridge_game_platforms') }}
    group by platform_id

),

platform_releases as (

    select
        platform_id,
        count(*) as release_event_count,
        min(release_date) as first_release_date,
        max(release_date) as latest_release_date
    from {{ ref('fct_game_releases') }}
    where platform_id is not null
    group by platform_id

)

select
    platforms.platform_id,
    platforms.name as platform_name,
    platforms.abbreviation as platform_abbreviation,
    platforms.category as platform_category,
    platforms.generation,
    coalesce(games.distinct_game_count, 0) as distinct_game_count,
    coalesce(releases.release_event_count, 0) as release_event_count,
    releases.first_release_date,
    releases.latest_release_date
from {{ ref('dim_platforms') }} as platforms
left join platform_games as games
    on platforms.platform_id = games.platform_id
left join platform_releases as releases
    on platforms.platform_id = releases.platform_id
