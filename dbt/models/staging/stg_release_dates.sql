select
    * except (id, game, platform, date, date_ts),
    id as release_date_id,
    game as game_id,
    platform as platform_id,
    date as release_date_raw,
    date_ts as release_timestamp,
    date(date_ts) as release_date
from {{ source('gaming_raw', 'release_dates') }}
