select
    * except (id, game, company, developer, publisher, porting, supporting),
    id as involved_company_id,
    game as game_id,
    company as company_id,
    developer as is_developer,
    publisher as is_publisher,
    porting as is_porting,
    supporting as is_supporting
from {{ source('gaming_raw', 'involved_companies') }}
