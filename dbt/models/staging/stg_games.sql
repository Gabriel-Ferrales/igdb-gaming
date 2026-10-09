select
    * except (id),
    id as game_id
from {{ source('gaming_raw', 'games') }}
