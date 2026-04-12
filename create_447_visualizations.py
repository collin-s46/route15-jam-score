from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from prepare_447_data import INPUT_PATH, add_features, create_daily_summary, load_and_clean


PREPARED_PATH = Path("447_data_prepared.csv")
DAILY_PATH = Path("447_daily_summary.csv")
OUTPUT_DIR = Path("447_visualizations")
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def load_prepared_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    if PREPARED_PATH.exists() and DAILY_PATH.exists():
        prepared = pd.read_csv(PREPARED_PATH)
        daily = pd.read_csv(DAILY_PATH)
        prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
        daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
        return prepared, daily

    clean_df = load_and_clean(INPUT_PATH)
    prepared = add_features(clean_df)
    daily = create_daily_summary(prepared)
    prepared.to_csv(PREPARED_PATH, index=False)
    daily.to_csv(DAILY_PATH, index=False)
    return prepared, daily


def create_visualizations(prepared: pd.DataFrame, daily: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")

    plt.figure(figsize=(14, 6))
    plt.plot(daily["date"], daily["avg_travel_time_min"], label="Daily average", linewidth=2)
    rolling = daily["avg_travel_time_min"].rolling(7, min_periods=1).mean()
    plt.plot(daily["date"], rolling, label="7-day rolling mean", linewidth=3)
    plt.title("Travel Time Trend")
    plt.xlabel("Date")
    plt.ylabel("Average Travel Time (minutes)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "01_travel_time_trend.png", dpi=180)
    plt.close()

    heatmap_df = (
        prepared.groupby(["day", "departure"], as_index=False)["travel_time_min"].mean()
        .pivot(index="day", columns="departure", values="travel_time_min")
        .reindex(DAY_ORDER)
    )
    plt.figure(figsize=(10, 6))
    sns.heatmap(heatmap_df, annot=True, fmt=".2f", cmap="YlOrRd")
    plt.title("Average Travel Time by Day and Departure")
    plt.xlabel("Departure")
    plt.ylabel("Day")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "02_day_departure_heatmap.png", dpi=180)
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.regplot(
        data=prepared,
        x="travel_time_min",
        y="jam_score",
        scatter_kws={"alpha": 0.6},
        line_kws={"color": "red"},
    )
    plt.title("Jam Score vs Travel Time")
    plt.xlabel("Travel Time (minutes)")
    plt.ylabel("Jam Score")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "03_jam_score_vs_travel_time.png", dpi=180)
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.boxplot(data=prepared, x="day", y="travel_time_min", order=DAY_ORDER)
    plt.title("Travel Time Distribution by Day")
    plt.xlabel("Day")
    plt.ylabel("Travel Time (minutes)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "04_travel_time_boxplot_by_day.png", dpi=180)
    plt.close()

    departure_profile = (
        prepared.groupby("departure", as_index=False)
        .agg(avg_travel_time_min=("travel_time_min", "mean"), avg_jam_score=("jam_score", "mean"))
        .sort_values("departure")
    )
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(
        departure_profile["departure"],
        departure_profile["avg_travel_time_min"],
        marker="o",
        linewidth=2,
        color="#1f77b4",
    )
    ax1.set_xlabel("Departure")
    ax1.set_ylabel("Average Travel Time (minutes)", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")

    ax2 = ax1.twinx()
    ax2.plot(
        departure_profile["departure"],
        departure_profile["avg_jam_score"],
        marker="s",
        linewidth=2,
        color="#ff7f0e",
    )
    ax2.set_ylabel("Average Jam Score", color="#ff7f0e")
    ax2.tick_params(axis="y", labelcolor="#ff7f0e")
    plt.title("Departure Profile: Travel Time vs Jam Score")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "05_departure_profile_dual_axis.png", dpi=180)
    plt.close()

    outliers = prepared[prepared["travel_time_outlier"]].copy()
    plt.figure(figsize=(14, 6))
    plt.plot(daily["date"], daily["avg_travel_time_min"], linewidth=2, label="Daily average")
    if not outliers.empty:
        plt.scatter(
            outliers["date"],
            outliers["travel_time_min"],
            color="red",
            alpha=0.7,
            label="Outlier points",
        )
    plt.title("Travel Time Timeline with Outlier Points")
    plt.xlabel("Date")
    plt.ylabel("Travel Time (minutes)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "06_timeline_with_outliers.png", dpi=180)
    plt.close()


def main() -> None:
    prepared, daily = load_prepared_data()
    create_visualizations(prepared, daily)
    print(f"Saved visualizations to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
