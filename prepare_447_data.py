from pathlib import Path

import pandas as pd


INPUT_PATH = Path("447_data.csv")
ROW_LEVEL_OUTPUT = Path("447_data_prepared.csv")
DAILY_OUTPUT = Path("447_daily_summary.csv")
EXPECTED_DEPARTURES_PER_DAY = 5


def load_and_clean(input_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path)

    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df = df.rename(columns={"travel_time": "travel_time_min"})

    for col in ["day", "departure"]:
        df[col] = df[col].astype(str).str.strip()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["jam_score"] = pd.to_numeric(df["jam_score"], errors="coerce")
    df["travel_time_min"] = pd.to_numeric(df["travel_time_min"], errors="coerce")

    # Keep only valid rows and remove impossible values.
    df = df.dropna(subset=["date", "day", "departure", "jam_score", "travel_time_min"])
    df = df[df["travel_time_min"] > 0]
    df = df[df["jam_score"] > 0]

    # If duplicate date/departure records exist, keep the most recent row.
    df = df.drop_duplicates(subset=["date", "departure"], keep="last")

    df = df.sort_values(["date", "departure"]).reset_index(drop=True)

    # Standardize weekday from the date to avoid string inconsistencies.
    df["day"] = df["date"].dt.day_name()

    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    departure_clock = pd.to_datetime(df["departure"], format="%H:%M", errors="coerce")
    df["departure_minutes"] = departure_clock.dt.hour * 60 + departure_clock.dt.minute
    df["departure_hour"] = departure_clock.dt.hour

    unique_departures = sorted(df["departure"].dropna().unique().tolist())
    slot_map = {slot: idx + 1 for idx, slot in enumerate(unique_departures)}
    df["departure_slot_rank"] = df["departure"].map(slot_map).astype("Int64")

    df["day_of_week_num"] = df["date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week_num"] >= 5

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.month_name()
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["quarter"] = df["date"].dt.quarter

    daily_counts = df.groupby("date")["departure"].transform("count")
    df["records_that_day"] = daily_counts
    df["is_complete_day"] = daily_counts.eq(EXPECTED_DEPARTURES_PER_DAY)

    day_avg_travel_time = df.groupby("day")["travel_time_min"].transform("mean")
    df["travel_time_vs_day_avg"] = (df["travel_time_min"] - day_avg_travel_time).round(2)
    df["travel_time_vs_overall_avg"] = (
        df["travel_time_min"] - df["travel_time_min"].mean()
    ).round(2)

    q1, q2 = df["travel_time_min"].quantile([0.33, 0.66])
    df["congestion_level"] = pd.cut(
        df["travel_time_min"],
        bins=[float("-inf"), q1, q2, float("inf")],
        labels=["low", "medium", "high"],
        include_lowest=True,
    )

    q1_t, q3_t = df["travel_time_min"].quantile([0.25, 0.75])
    iqr = q3_t - q1_t
    lower_bound = q1_t - 1.5 * iqr
    upper_bound = q3_t + 1.5 * iqr
    df["travel_time_outlier"] = ~df["travel_time_min"].between(lower_bound, upper_bound)

    return df


def create_daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    daily = (
        df.groupby("date", as_index=False)
        .agg(
            day=("day", "first"),
            records=("departure", "count"),
            avg_travel_time_min=("travel_time_min", "mean"),
            min_travel_time_min=("travel_time_min", "min"),
            max_travel_time_min=("travel_time_min", "max"),
            avg_jam_score=("jam_score", "mean"),
            min_jam_score=("jam_score", "min"),
            max_jam_score=("jam_score", "max"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    daily["is_complete_day"] = daily["records"].eq(EXPECTED_DEPARTURES_PER_DAY)
    daily["day_of_week_num"] = daily["date"].dt.dayofweek
    daily["year"] = daily["date"].dt.year
    daily["month"] = daily["date"].dt.month
    daily["week_of_year"] = daily["date"].dt.isocalendar().week.astype(int)

    rounded_cols = [
        "avg_travel_time_min",
        "min_travel_time_min",
        "max_travel_time_min",
        "avg_jam_score",
        "min_jam_score",
        "max_jam_score",
    ]
    daily[rounded_cols] = daily[rounded_cols].round(2)

    return daily


def main() -> None:
    clean_df = load_and_clean(INPUT_PATH)
    prepared_df = add_features(clean_df)
    daily_summary = create_daily_summary(prepared_df)

    prepared_df = prepared_df.copy()
    daily_summary = daily_summary.copy()
    prepared_df["date"] = prepared_df["date"].dt.strftime("%Y-%m-%d")
    daily_summary["date"] = daily_summary["date"].dt.strftime("%Y-%m-%d")

    prepared_df.to_csv(ROW_LEVEL_OUTPUT, index=False)
    daily_summary.to_csv(DAILY_OUTPUT, index=False)

    print(f"Saved: {ROW_LEVEL_OUTPUT} ({len(prepared_df)} rows)")
    print(f"Saved: {DAILY_OUTPUT} ({len(daily_summary)} rows)")


if __name__ == "__main__":
    main()
