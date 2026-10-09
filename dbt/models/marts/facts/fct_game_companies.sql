/*
Model: fct_game_companies

Purpose:
Represent company participation in games as a factless fact table enriched
with additive role indicators.

Grain:
One row per involved_company_id.

Primary key:
involved_company_id.

Foreign keys:
- game_id -> dim_games.game_id
- company_id -> dim_companies.company_id

Inputs:
- int_game_companies

Important metric behavior:
Role counts equal 1 when the corresponding boolean is true and 0 otherwise.
They are additive across relationship rows, while the booleans preserve the
original relationship attributes.
*/

select
    involved_company_id,
    game_id,
    company_id,
    is_developer,
    is_publisher,
    is_porting,
    is_supporting,
    if(is_developer, 1, 0) as developer_count,
    if(is_publisher, 1, 0) as publisher_count,
    if(is_porting, 1, 0) as porting_count,
    if(is_supporting, 1, 0) as supporting_count
from {{ ref('int_game_companies') }}
