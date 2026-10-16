# Data Quality & Limitations

## Validation and audit scope

The loader checks staging record counts, null IDs, and duplicate IDs before merging a batch. dbt declares `not_null`, `unique`, `relationships`, and composite-key tests. These checks validate the modeled data; they do not independently verify every source attribute.

The read-only audit conducted on **October 12, 2026** investigated a historical loaded snapshot, not live IGDB data. Its aggregation validation covered `platform_performance` and `games_release_trends`; the results should not be generalized to uninvestigated marts or future loads.

## Verified snapshot findings

| Finding | Observed result |
| --- | --- |
| Raw release records → release fact records | 574,447 → 572,631 (99.68% retained) |
| Releases excluded because referenced games were not loaded | 1,816 |
| Fact releases with missing dates | 40,071 |
| Fact releases with partial date precision | 55,841 |
| Fact releases dated after the audit date | 4,931 |
| Timestamp conversion / raw-to-fact date discrepancies | 0 observed |
| Aggregation discrepancies in checked platform and yearly release marts | 0 observed |

The 1,816 excluded release records all referenced games absent from the loaded games table. This matches the inner join in `int_game_releases`. There were no observed raw-to-fact changes for retained records in the audited lineage comparison.

## Source dates and precision

IGDB is an external source whose metadata can be incomplete or inconsistent. The 55,841 partial-precision fact dates were inferred from source display strings indicating **year, quarter, or month**, rather than populated category codes. This was an audit analysis, not a precision classification implemented in the marts.

The pipeline preserves source-provided date values without inventing corrections. A typed calendar date does not establish exact day-level precision. Scheduled or approximate future dates are not confirmed releases; the 4,931 future-dated fact records were measured relative to October 12, 2026.

Missing dates remain null in `fct_game_releases` and are excluded from `games_release_trends`. Platform-associated release dates describe recorded game release events, not verified platform commercial launch dates. The audit did not establish that all historical source dates are correct.

## Coverage and relationship limitations

Releases without matching loaded games are excluded by the current intermediate model. The audit did not determine whether the missing games reflect source availability, ingestion coverage, or API filtering.

Distinct source release IDs can share a game/platform/date combination. Source relationship arrays do not always agree with release records, so platform catalog membership and release events are separate analytical concepts. Counts of release events should not be interpreted as counts of unique games.

## Rating and aggregation interpretation

Rating models contain the current loaded state only. `snapshot_date` records the dbt build date; it does not provide retained rating history. `top_rated_games` applies no minimum vote threshold, so consumers should filter by rating count when comparing rankings.

A multi-genre game contributes to each assigned genre. Genre averages weight each rated game equally rather than by vote count, and genre game counts should not be summed into a global unique-game total.

These findings validate the checked pipeline calculations, not the accuracy of every source record or the quality of live IGDB data. See the [data dictionary](data_dictionary.md), [marts model](data_model/marts_model.md), and [project README](../README.md).
