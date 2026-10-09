/*
Model: int_game_companies

Purpose:
Prepare company participation records for each game.

Grain:
One row per involved_company_id.

Business key:
involved_company_id.

Inputs:
- stg_involved_companies

Future use:
- fct_game_companies
*/

with involved_companies as (

    select
        involved_company_id,
        game_id,
        company_id,
        is_developer,
        is_publisher,
        is_porting,
        is_supporting,
        updated_at,
        _loaded_at
    from {{ ref('stg_involved_companies') }}

),

deduplicated as (

    select
        involved_company_id,
        game_id,
        company_id,
        coalesce(is_developer, false) as is_developer,
        coalesce(is_publisher, false) as is_publisher,
        coalesce(is_porting, false) as is_porting,
        coalesce(is_supporting, false) as is_supporting,
        row_number() over (
            partition by involved_company_id
            order by updated_at desc, _loaded_at desc
        ) as row_number
    from involved_companies
    where involved_company_id is not null
      and game_id is not null
      and company_id is not null

)

select
    involved_company_id,
    game_id,
    company_id,
    is_developer,
    is_publisher,
    is_porting,
    is_supporting
from deduplicated
where row_number = 1
