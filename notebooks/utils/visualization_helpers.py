"""Visualization helper functions for time-based analysis.

This module provides reusable visualization functions for creating
interactive time-based plots with computer activity and commit overlays.
"""

from typing import List, Optional, Tuple, Union

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def safe_to_datetime_amsterdam(data: Union[pd.Series, str, List[str]], column_name: str = "timestamp") -> pd.Series:
    """Safely convert data to timezone-aware Amsterdam datetime.

    This function handles both timezone-naive and timezone-aware input data,
    ensuring consistent Amsterdam timezone output without raising errors.

    Args:
        data: Input data to convert (Series, string, or list of strings)
        column_name: Name of the column for error messages

    Returns:
        pandas Series with timezone-aware Amsterdam datetime

    Raises:
        ValueError: If data cannot be converted to datetime
    """
    # Convert to pandas Series if not already
    if not isinstance(data, pd.Series):
        data = pd.Series(data)

    # Convert to datetime first
    dt_series = pd.to_datetime(data, errors="coerce")

    # Check if any values are already timezone-aware
    has_timezone = dt_series.dt.tz is not None

    if has_timezone:
        # If already timezone-aware, convert to Amsterdam timezone
        return dt_series.dt.tz_convert("Europe/Amsterdam")
    else:
        # If timezone-naive, assume Amsterdam timezone and localize
        return dt_series.dt.tz_localize("Europe/Amsterdam")


def setup_plot_style():
    """Set up consistent plot styling for time-based visualizations."""
    plt.style.use("default")
    sns.set_palette("husl")

    # Set figure size and DPI for better quality
    plt.rcParams["figure.figsize"] = (15, 8)
    plt.rcParams["figure.dpi"] = 100
    plt.rcParams["font.size"] = 10
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["axes.labelsize"] = 12
    plt.rcParams["xtick.labelsize"] = 10
    plt.rcParams["ytick.labelsize"] = 10
    plt.rcParams["legend.fontsize"] = 10


def create_computer_activity_timeline(
    work_sessions_df: pd.DataFrame, start_date: str, end_date: str, ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """Create timeline visualization of computer activity periods.

    Args:
        work_sessions_df: DataFrame with work session data
        start_date: Start date for the timeline
        end_date: End date for the timeline
        ax: Optional matplotlib axes to plot on

    Returns:
        matplotlib axes with computer activity timeline
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(15, 8))

    # Filter work sessions by date range
    start_dt = safe_to_datetime_amsterdam(start_date, "start_date").iloc[0]
    end_dt = safe_to_datetime_amsterdam(end_date, "end_date").iloc[0]

    # Filter sessions that overlap with the date range
    mask = (work_sessions_df["start_time"] <= end_dt) & (work_sessions_df["end_time"] >= start_dt)
    filtered_sessions = work_sessions_df[mask].copy()

    if filtered_sessions.empty:
        ax.text(0.5, 0.5, "No work sessions found in date range", ha="center", va="center", transform=ax.transAxes)
        return ax

    # Create timeline bars for each work session
    for idx, session in filtered_sessions.iterrows():
        # Calculate the position and width of the bar
        start_time = max(session["start_time"], start_dt)
        end_time = min(session["end_time"], end_dt)

        # Convert to matplotlib date format for x-axis (dates)
        start_date_mpl = mdates.date2num(start_time.date())
        end_date_mpl = mdates.date2num(end_time.date())

        # Calculate time of day for y-axis (0-24 hours)
        start_hour = start_time.hour + start_time.minute / 60.0
        end_hour = end_time.hour + end_time.minute / 60.0

        # Handle sessions that cross midnight
        if start_time.date() != end_time.date():
            # Split into two bars: one for each day
            # First day: from start time to midnight
            first_day_end_hour = 24.0
            ax.bar(
                start_date_mpl,
                first_day_end_hour - start_hour,
                bottom=start_hour,
                width=0.8,
                alpha=0.6,
                color="lightblue",
                edgecolor="blue",
                linewidth=0.5,
            )

            # Second day: from midnight to end time
            ax.bar(end_date_mpl, end_hour, bottom=0, width=0.8, alpha=0.6, color="lightblue", edgecolor="blue", linewidth=0.5)
        else:
            # Single day session
            ax.bar(
                start_date_mpl,
                end_hour - start_hour,
                bottom=start_hour,
                width=0.8,
                alpha=0.6,
                color="lightblue",
                edgecolor="blue",
                linewidth=0.5,
            )

    # Set up the plot
    ax.set_xlim(mdates.date2num(start_dt.date()), mdates.date2num(end_dt.date()) + 1)
    ax.set_ylim(0, 24)

    # Format x-axis (dates)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Format y-axis (time of day)
    ax.set_ylabel("Time of Day (Hours)")
    ax.set_xlabel("Date")
    ax.set_title(f"Computer Activity Timeline ({start_date} to {end_date})")

    # Set y-axis ticks for hours
    ax.set_yticks(range(0, 25, 2))  # Every 2 hours
    ax.set_yticklabels([f"{h:02d}:00" for h in range(0, 25, 2)])

    # Add grid
    ax.grid(True, alpha=0.3)

    return ax


def create_commit_overlay(
    commits_df: pd.DataFrame,
    work_sessions_df: pd.DataFrame,
    start_date: str,
    end_date: str,
    ax: Optional[plt.Axes] = None,
    active_repos: Optional[List[str]] = None,
) -> plt.Axes:
    """Create commit markers overlay on the computer activity timeline.

    Args:
        commits_df: DataFrame with commits data
        work_sessions_df: DataFrame with work session data (for reference)
        start_date: Start date for the timeline
        end_date: End date for the timeline
        ax: Optional matplotlib axes to plot on
        active_repos: Optional list of active repositories to show

    Returns:
        matplotlib axes with commit overlay markers
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(15, 8))

    # Filter commits by date range
    start_dt = safe_to_datetime_amsterdam(start_date, "start_date").iloc[0]
    end_dt = safe_to_datetime_amsterdam(end_date, "end_date").iloc[0]

    mask = (commits_df["timestamp"] >= start_dt) & (commits_df["timestamp"] <= end_dt)
    filtered_commits = commits_df[mask].copy()

    # Filter by active repositories if specified
    if active_repos:
        filtered_commits = filtered_commits[filtered_commits["repo_name"].isin(active_repos)].copy()

    if filtered_commits.empty:
        return ax

    # Get unique repositories and assign colors/markers
    unique_repos = filtered_commits["repo_name"].unique()
    repo_colors = sns.color_palette("husl", len(unique_repos))
    repo_markers = ["o", "s", "^", "D", "v", "<", ">", "p", "*", "h"]

    repo_style_map = {}
    for i, repo in enumerate(unique_repos):
        repo_style_map[repo] = {"color": repo_colors[i % len(repo_colors)], "marker": repo_markers[i % len(repo_markers)]}

    # Plot commits as markers
    for repo in unique_repos:
        repo_commits = filtered_commits[filtered_commits["repo_name"] == repo]
        style = repo_style_map[repo]

        # Convert timestamps to matplotlib date format for x-axis
        commit_dates = [mdates.date2num(ts.date()) for ts in repo_commits["timestamp"]]

        # Calculate time of day for y-axis (0-24 hours)
        commit_hours = [ts.hour + ts.minute / 60.0 for ts in repo_commits["timestamp"]]

        # Plot markers
        ax.scatter(
            commit_dates,
            commit_hours,
            c=[style["color"]],
            marker=style["marker"],
            s=100,
            alpha=0.8,
            edgecolors="black",
            linewidth=0.5,
            label=repo,
        )

    # Add legend if we have repositories
    if len(unique_repos) > 0:
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

    return ax


def create_combined_timeline_plot(
    work_sessions_df: pd.DataFrame,
    commits_df: pd.DataFrame,
    start_date: str,
    end_date: str,
    active_repos: Optional[List[str]] = None,
    figsize: Tuple[int, int] = (16, 10),
) -> plt.Figure:
    """Create combined timeline plot with computer activity and commit overlays.

    Args:
        work_sessions_df: DataFrame with work session data
        commits_df: DataFrame with commits data
        start_date: Start date for the timeline
        end_date: End date for the timeline
        active_repos: Optional list of active repositories to show
        figsize: Figure size tuple

    Returns:
        matplotlib figure with combined timeline plot
    """
    setup_plot_style()

    fig, ax = plt.subplots(figsize=figsize)

    # Create computer activity timeline
    ax = create_computer_activity_timeline(work_sessions_df, start_date, end_date, ax)

    # Add commit overlay
    ax = create_commit_overlay(commits_df, work_sessions_df, start_date, end_date, ax, active_repos)

    # Adjust layout
    plt.tight_layout()

    return fig


def create_daily_activity_summary(
    work_sessions_df: pd.DataFrame, commits_df: pd.DataFrame, start_date: str, end_date: str
) -> pd.DataFrame:
    """Create daily summary of computer activity and commits.

    Args:
        work_sessions_df: DataFrame with work session data
        commits_df: DataFrame with commits data
        start_date: Start date for the summary
        end_date: End date for the summary

    Returns:
        DataFrame with daily activity summary
    """
    # Create date range
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")

    summary_data = []

    for date in date_range:
        date_str = date.strftime("%Y-%m-%d")

        # Filter work sessions for this date
        day_sessions = work_sessions_df[(work_sessions_df["date"].dt.date == date.date())]

        # Filter commits for this date
        day_commits = commits_df[(commits_df["timestamp"].dt.date == date.date())]

        # Calculate summary metrics
        total_work_hours = day_sessions["duration_hours"].sum() if not day_sessions.empty else 0
        session_count = len(day_sessions)
        commit_count = len(day_commits)
        unique_repos = day_commits["repo_name"].nunique() if not day_commits.empty else 0

        summary_data.append(
            {
                "date": date_str,
                "total_work_hours": total_work_hours,
                "session_count": session_count,
                "commit_count": commit_count,
                "unique_repos": unique_repos,
                "repos": list(day_commits["repo_name"].unique()) if not day_commits.empty else [],
            }
        )

    return pd.DataFrame(summary_data)


def plot_daily_summary(summary_df: pd.DataFrame, figsize: Tuple[int, int] = (15, 10)) -> plt.Figure:
    """Plot daily activity summary with multiple subplots.

    Args:
        summary_df: DataFrame with daily activity summary
        figsize: Figure size tuple

    Returns:
        matplotlib figure with daily summary plots
    """
    setup_plot_style()

    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle("Daily Activity Summary", fontsize=16)

    # Convert date column to datetime
    summary_df["date"] = pd.to_datetime(summary_df["date"])

    # Plot 1: Work hours per day
    axes[0, 0].bar(summary_df["date"], summary_df["total_work_hours"], alpha=0.7, color="lightblue")
    axes[0, 0].set_title("Work Hours per Day")
    axes[0, 0].set_ylabel("Hours")
    axes[0, 0].tick_params(axis="x", rotation=45)

    # Plot 2: Session count per day
    axes[0, 1].bar(summary_df["date"], summary_df["session_count"], alpha=0.7, color="lightgreen")
    axes[0, 1].set_title("Work Sessions per Day")
    axes[0, 1].set_ylabel("Number of Sessions")
    axes[0, 1].tick_params(axis="x", rotation=45)

    # Plot 3: Commit count per day
    axes[1, 0].bar(summary_df["date"], summary_df["commit_count"], alpha=0.7, color="lightcoral")
    axes[1, 0].set_title("Commits per Day")
    axes[1, 0].set_ylabel("Number of Commits")
    axes[1, 0].tick_params(axis="x", rotation=45)

    # Plot 4: Unique repositories per day
    axes[1, 1].bar(summary_df["date"], summary_df["unique_repos"], alpha=0.7, color="lightyellow")
    axes[1, 1].set_title("Active Repositories per Day")
    axes[1, 1].set_ylabel("Number of Repositories")
    axes[1, 1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    return fig
