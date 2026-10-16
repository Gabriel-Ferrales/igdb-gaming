# Data dictionary

IGDB IDs are retained as analytical keys. dbt staging and intermediate models are views; dimensions, bridges, facts, and analytics models are tables. The SQL models define the complete column projections; this dictionary covers the keys and measures needed to interpret the dashboard.

## Source and staging

The six raw endpoint tables are `games`, `platforms`, `genres`, `companies`, `involved_companies`, and `release_dates`. Staging renames `id` to an entity-specific key. In involved companies, `game` and `company` become `game_id` and `company_id`; source role flags become `is_developer`, `is_publisher`, `is_porting`, and `is_supporting`.

Release staging renames `game`, `platform`, `date`, and `date_ts` to `game_id`, `platform_id`, `release_date_raw`, and `release_timestamp`. `release_date` is derived from that timestamp as a BigQuery `DATE`.

## Dimensions and bridges

| Model | Key / grain | Descriptive fields |
| --- | --- | --- |
| `dim_games` | `game_id` | `name`, `slug`, `summary`, `category`, `status`, `first_release_date`, `first_release_date_ts`, creation/update values and timestamps |
| `dim_platforms` | `platform_id` | `name`, `slug`, `abbreviation`, `alternative_name`, `category`, `generation`, `platform_family`, `platform_logo`, creation/update values and timestamps |
| `dim_genres` | `genre_id` | `name`, `slug`, creation/update values and timestamps |
| `dim_companies` | `company_id` | `name`, `slug`, `description`, `country`, `parent`, `start_date`, `start_date_ts`, `changed_company_id`, `logo`, `url`, creation/update values and timestamps |
| `bridge_game_platforms` | `game_id` + `platform_id` | Distinct catalog membership pairs from the games array |
| `bridge_game_genres` | `game_id` + `genre_id` | Distinct genre membership pairs from the games array |

Dimensions choose the latest loaded row by source `updated_at`, then `_loaded_at`. Referenced metadata IDs such as `platform_family` and `logo` do not imply separate dimensions exist in this project.

## Facts

| Model | Grain | Fields and semantics |
| --- | --- | --- |
| `fct_game_releases` | `release_date_id` | `game_id`, `platform_id`, `release_date_raw` (Unix integer), `release_timestamp` (UTC), `release_date` (calendar date), `region`, `release_category`, `release_count` (always 1) |
| `fct_game_companies` | `involved_company_id` | `game_id`, `company_id`, four `is_*` role flags, and corresponding `*_count` indicators (0 or 1 per relationship row) |
| `fct_game_ratings` | `game_id` | `rating`, `rating_count`, `aggregated_rating`, `aggregated_rating_count`, `snapshot_date` (build date) |

Release dates remain nullable. `release_category` comes from the source category field, but category was unpopulated in the audited release snapshot and cannot supply precision labels for it. Region was also unpopulated. Source `human`, `m`, `y`, and `status` are not projected into the release fact. Display-string precision inference was an audit analysis, not an implemented mart feature.

Release events can repeat a game across platforms, dates, regions, or categories. Unique release IDs do not guarantee a unique game/platform/date combination. Company role indicators are additive across involvement records; distinct-game role counts in analytics deduplicate those records. Rating facts retain current state only and do not accumulate snapshots.

## Analytics measures

| Model | Key / grain | Measures |
| --- | --- | --- |
| `games_release_trends` | `release_year` | `release_count`: fact rows with a date in the year; `distinct_games_released`: distinct games within that year; `distinct_platforms`: distinct non-null platforms with release events |
| `genre_performance` | `genre_id` | `distinct_game_count`; games with user/critic scores; average scores over non-null game scores; `total_user_rating_count`: sum of user vote counts |
| `platform_performance` | `platform_id` | `distinct_game_count`: bridge catalog membership; `release_event_count`: release fact rows; `first_release_date` / `latest_release_date`: min/max non-null recorded game event dates |
| `company_performance` | `company_id` | `distinct_game_count` and `developer_game_count`, `publisher_game_count`, `porting_game_count`, `supporting_game_count`: distinct games for each role |
| `top_rated_games` | `game_id` | `game_name`, typed game `first_release_date`, `user_rating`, `user_rating_count`, `aggregated_rating`, `aggregated_rating_count`, `rating_snapshot_date` |

Platform event dates are not verified hardware launch dates. Genre averages weight each rated game equally, not by vote count; a game belongs to every assigned genre. No minimum vote threshold is imposed by `top_rated_games`. Null scores mean unavailable data, not zero scores.

See [model relationships](data_model/marts_model.md) and the [README audit summary](../README.md#data-quality--limitations) for interpretation limits.
