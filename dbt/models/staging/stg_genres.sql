select
    * except (id),
    id as genre_id
from {{ source('gaming_raw', 'genres') }}
