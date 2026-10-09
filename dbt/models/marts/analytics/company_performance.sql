/*
Model: company_performance

Purpose:
Summarize current company participation across games by involvement role.

Grain:
One row per company_id.

Metric behavior:
All measures count distinct game IDs. The source fact can contain more than one
involvement record for the same company and game, so counting fact rows would
overstate participation.
*/

with company_metrics as (

    select
        company_id,
        count(distinct game_id) as distinct_game_count,
        count(distinct if(is_developer, game_id, null)) as developer_game_count,
        count(distinct if(is_publisher, game_id, null)) as publisher_game_count,
        count(distinct if(is_porting, game_id, null)) as porting_game_count,
        count(distinct if(is_supporting, game_id, null)) as supporting_game_count
    from {{ ref('fct_game_companies') }}
    group by company_id

)

select
    companies.company_id,
    companies.name as company_name,
    companies.country,
    coalesce(metrics.distinct_game_count, 0) as distinct_game_count,
    coalesce(metrics.developer_game_count, 0) as developer_game_count,
    coalesce(metrics.publisher_game_count, 0) as publisher_game_count,
    coalesce(metrics.porting_game_count, 0) as porting_game_count,
    coalesce(metrics.supporting_game_count, 0) as supporting_game_count
from {{ ref('dim_companies') }} as companies
left join company_metrics as metrics
    on companies.company_id = metrics.company_id
