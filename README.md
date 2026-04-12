![catplot for travel time vs. day](https://github.com/collin-s46/route15-jam-score/blob/main/images/catplot1.png)

![bargraph for travel time vs. day](https://github.com/collin-s46/route15-jam-score/blob/main/images/bargraph1.png)

![lineplot for departure time vs. travel time](https://github.com/collin-s46/route15-jam-score/blob/main/images/lineplot_departure.png)

## Quick data prep for dashboard/modeling

Run:

```bash
python prepare_447_data.py
```

This generates:

- `447_data_prepared.csv` (row-level cleaned + engineered features)
- `447_daily_summary.csv` (daily aggregated metrics)

### Added features in `447_data_prepared.csv`

- Calendar: `year`, `month`, `month_name`, `week_of_year`, `quarter`
- Weekday/time: `day_of_week_num`, `departure_minutes`, `departure_hour`, `departure_slot_rank`
- Data quality/completeness: `records_that_day`, `is_complete_day`
- Modeling helpers: `travel_time_vs_day_avg`, `travel_time_vs_overall_avg`, `congestion_level`, `travel_time_outlier`

## Visualization pack

Run:

```bash
python create_447_visualizations.py
```

All graphs are saved in:

- `447_visualizations/`
