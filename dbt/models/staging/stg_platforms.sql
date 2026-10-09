select
    * except (id),
    id as platform_id
from {{ source('gaming_raw', 'platforms') }}
