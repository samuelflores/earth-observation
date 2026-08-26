import importlib
import numpy as np 
import pandas 
importlib.reload(pandas)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import inspect
import Constants

def get_warm_dry_season(year):

    year_offset = year - 2025

    season_start = (
        Constants.warmDryStart2025
        + pandas.DateOffset(years=year_offset)
    )

    season_end = (
        Constants.warmDryEnd2025
        + pandas.DateOffset(years=year_offset)
    )

    return season_start, season_end

# This makes a horizontal line representing the season average of a certain quantity. Returns that quantity
#start date of season, end date of season, dataframe containing daily quantity, matplotlib axis
def add_season_avg_qty_to_axis(my_start_date,my_end_date,my_df,plot_name,my_ax,my_color,line_style,my_label,offset=0):
    my_plot_avg = my_df.loc[(my_df["date"] >= my_start_date) & (my_df["date"] <= my_end_date), plot_name].mean()
    #for 
    my_plot_std_dev = my_df.loc[(my_df["date"] >= my_start_date) & (my_df["date"] <= my_end_date), plot_name].std()
    print("for plot ",plot_name," my_plot_std_dev = ",my_plot_std_dev)

    print(f"[Cell Line {inspect.currentframe().f_lineno}] .. my_plot_avg= ",my_plot_avg)
    if pandas.notna(my_plot_avg):
        # value line:
        my_ax.hlines(y=my_plot_avg, xmin=my_start_date, xmax=my_end_date,
              colors=my_color, linewidth=2.2,linestyle=line_style)
        # high end of error
        #my_ax.hlines(y=my_plot_avg+my_plot_std_dev, xmin=my_start_date, xmax=my_end_date,
        #      colors=my_color, linewidth=2.2,linestyle=line_style)
        #low end of error
        #my_ax.hlines(y=my_plot_avg-my_plot_std_dev, xmin=my_start_date, xmax=my_end_date,
        #      colors=my_color, linewidth=2.2,linestyle=line_style)
        my_ax.vlines(x=(my_end_date - (my_end_date-my_start_date)/2 +  pandas.DateOffset(days = offset)) , ymin=my_plot_avg-my_plot_std_dev, ymax = my_plot_avg+my_plot_std_dev,
              colors=my_color, linewidth=2.2,linestyle=line_style)
        #ax.text(my_start_date + (my_end_date - my_start_date)/2, my_plot_avg,
        #    f"{my_label} = {my_plot_avg:.3f}", ha="center", va="top",
        #    fontsize=9, color=my_color)
        return my_plot_avg


# Makes a line plot of quantities averaged over a certain season.
def plot_season_averages(my_start_date,my_end_date,my_df,aoi_name,my_ax,my_color,line_style,my_label,offset=0,my_verticalalignment = "bottom"):   
    SSEDA = [] # was season_start_end_date_array
    endYear = pandas.to_datetime(my_end_date).year
    #print("latest_year = ",latest_year)
    startYear = pandas.to_datetime(my_start_date).year
    for year in range( endYear,startYear-1,-1) : 
        season_start, season_end = get_warm_dry_season(year)
        season_middle = season_start + (season_end - season_start) / 2
        SSEDA.insert(0,
            (season_start, #Constants.warmDryStart2025 - pandas.DateOffset(years = endYear-year),  #season start
             season_end, #Constants.warmDryEnd2025   - pandas.DateOffset(years = endYear-year),  #season end 
             season_middle  #(season_start+season_end)/2 #Constants.warmDryStart2025 - pandas.DateOffset(years = endYear-year) + (Constants.warmDryEnd2025 - Constants.warmDryStart2025)/2 #season middle
        ))
        add_season_avg_qty_to_axis(SSEDA[0][0],SSEDA[0][1],my_df,aoi_name,my_ax,my_color,line_style,my_label,offset)
        if len(SSEDA) > 1 :
            print("0 start, end, middle dates: ",SSEDA[0][0],SSEDA[0][1], SSEDA[0][2])
            print(" value ", my_df.loc[(my_df["date"] >= SSEDA[0][0]) & (my_df["date"] <= SSEDA[0][1]), aoi_name].mean())
            print("1 start, end, middle dates: ",SSEDA[1][0],SSEDA[1][1], SSEDA[1][2])
            print(" value ", my_df.loc[(my_df["date"] >= SSEDA[1][0]) & (my_df["date"] <= SSEDA[1][1]), aoi_name].mean())
            my_ax.plot(
                [SSEDA[0][2], 
                SSEDA[1][2]],  
                [my_df.loc[(my_df["date"] >= SSEDA[0][0]) & (my_df["date"] <= SSEDA[0][1]), aoi_name].mean(), 
                my_df.loc[(my_df["date"] >= SSEDA[1][0]) & (my_df["date"] <= SSEDA[1][1]), aoi_name].mean()],
                linestyle=line_style,
                #linewidth=4,
                color = my_color    
               )   
        else : # this is the latest year
            my_plot_avg = my_df.loc[(my_df["date"] >= SSEDA[0][0]) & (my_df["date"] <= SSEDA[0][1]), aoi_name].mean()
            my_ax.text(SSEDA[0][2] ,my_plot_avg,
            f" {my_label}\n", ha="left", va=my_verticalalignment,
            fontsize=12,color=my_color)
        print ("SSEDA =",SSEDA)

def plot_season_precipitation(my_start_date,my_end_date, my_ax,my_label="Dry season",my_color="black",line_style="solid"):   
    SSEDA = [] # was season_start_end_date_array
    endYear = pandas.to_datetime(my_end_date).year
    startYear = pandas.to_datetime(my_start_date).year
    for year in range( endYear,startYear-1,-1) : 
        season_start, season_end = get_warm_dry_season(year)
        season_middle = season_start + (season_end - season_start) / 2
        SSEDA.insert(0,
            (season_start, #Constants.warmDryStart2025 - pandas.DateOffset(years = endYear-year),  #season start
             season_end, #Constants.warmDryEnd2025   - pandas.DateOffset(years = endYear-year),  #season end 
             season_middle   #(season_start+season_end)/2 #Constants.warmDryStart2025 - pandas.DateOffset(years = endYear-year) + (Constants.warmDryEnd2025 - Constants.warmDryStart2025)/2 #season middle
        ))
        # draw a line across the interval at 90% height of NDMI axis
        my_ax.hlines(y=27  , xmin=SSEDA[0][0], xmax=SSEDA[0][1], color=my_color, lw=1.2)
        # put label slightly above the line
        #my_ax.text(SSEDA[0][2],ymax , my_label, ha="center", va="bottom", fontsize=9)
        my_ax.axvspan(SSEDA[0][0],SSEDA[0][1],  fill=1, color = my_color )	

def indicate_seasons_box(
    my_start_date,
    my_end_date,
    my_ax,
    my_label="Dry season",
    my_color="black",
    line_style="solid"
):

    endYear = pandas.to_datetime(my_end_date).year
    startYear = pandas.to_datetime(my_start_date).year

    for year in range(startYear, endYear + 1):

        year_offset = year - 2025
        season_start, season_end = get_warm_dry_season(year)

        my_ax.axvspan(
            season_start,
            season_end,
            fill=True,
            color=my_color
        )

def indicate_seasons_box_old(my_start_date,my_end_date, my_ax,my_label="Dry season",my_color="black",line_style="solid"):   
    SSEDA = [] # was season_start_end_date_array
    endYear = pandas.to_datetime(my_end_date).year
    startYear = pandas.to_datetime(my_start_date).year
    for year in range( endYear,startYear-1,-1) : 
        SSEDA.insert(0,
            (Constants.warmDryStart2025 - pandas.DateOffset(years = endYear-year),  #season start
             Constants.warmDryEnd2025   - pandas.DateOffset(years = endYear-year),  #season end 
             Constants.warmDryStart2025 - pandas.DateOffset(years = endYear-year) + (Constants.warmDryEnd2025 - Constants.warmDryStart2025)/2 #season middle
        ))
        # draw a line across the interval at 90% height of NDMI axis
        my_ax.hlines(y=27  , xmin=SSEDA[0][0], xmax=SSEDA[0][1], color=my_color, lw=1.2)
        # put label slightly above the line
        #my_ax.text(SSEDA[0][2],ymax , my_label, ha="center", va="bottom", fontsize=9)
        my_ax.axvspan(SSEDA[0][0],SSEDA[0][1],  fill=1, color = my_color )	

def indicate_seasons(my_start_date,my_end_date,my_ax,my_label="Dry season",my_color="black",line_style="solid"):   
    SSEDA = [] # was season_start_end_date_array
    endYear = pandas.to_datetime(my_end_date).year
    startYear = pandas.to_datetime(my_start_date).year
    for year in range( endYear,startYear-1,-1) : 
        season_start, season_end = get_warm_dry_season(year)
        season_middle = (
            season_start
            + (season_end - season_start) / 2
        )
        SSEDA.insert(0,
            (season_start, #Constants.warmDryStart2025 - pandas.DateOffset(years = endYear-year),  #season start
             season_end, #Constants.warmDryEnd2025   - pandas.DateOffset(years = endYear-year),  #season end 
             season_middle #Constants.warmDryStart2025 - pandas.DateOffset(years = endYear-year) + (Constants.warmDryEnd2025 - Constants.warmDryStart2025)/2 #season middle
        ))
        # draw a line across the interval at 90% height of NDMI axis
        my_ax.hlines(y=27  , xmin=SSEDA[0][0], xmax=SSEDA[0][1], color=my_color, lw=1.2)
        # put label slightly above the line
        my_ax.text(SSEDA[0][2],28 , my_label, ha="center", va="bottom", fontsize=9)

def plot_season_climate_averages(
    my_start_date,
    my_end_date,
    dates,
    temperatures,
    precipitations,
    temp_ax,
    precip_ax,
    temp_color="red",
    precip_color="tab:blue",
    linewidth=3.0,
    annotate=True
):
    """
    Plot mean temperature and mean daily precipitation for each dry season.

    Temperature averages are drawn on temp_ax.
    Precipitation averages are drawn on precip_ax.

    Dry-season dates are derived from:
        Constants.warmDryStart2025
        Constants.warmDryEnd2025

    Parameters
    ----------
    my_start_date, my_end_date
        Overall plotting date range.

    dates
        Iterable of daily datetime-like values.

    temperatures
        Daily temperature values corresponding to dates.

    precipitations
        Daily precipitation values corresponding to dates.

    temp_ax
        Matplotlib axis used for temperature.

    precip_ax
        Matplotlib axis used for precipitation.

    annotate
        If True, write the seasonal averages above the lines.
    """

    start_year = pandas.to_datetime(my_start_date).year
    end_year   = pandas.to_datetime(my_end_date).year

    dates_series = pandas.to_datetime(pandas.Series(dates))

    temp_series = pandas.Series(
        temperatures,
        index=dates_series,
        dtype="float64"
    )

    precip_series = pandas.Series(
        precipitations,
        index=dates_series,
        dtype="float64"
    )

    for year in range(start_year, end_year + 1):

        year_offset = 2025 - year
        season_start, season_end = get_warm_dry_season(year)

        # Don't draw seasons completely outside the requested plot range
        if season_end < pandas.to_datetime(my_start_date):
            continue

        if season_start > pandas.to_datetime(my_end_date):
            continue

        season_middle = (
            season_start
            + (season_end - season_start) / 2
        )

        temp_mask = (
            (temp_series.index >= season_start)
            & (temp_series.index <= season_end)
        )

        precip_mask = (
            (precip_series.index >= season_start)
            & (precip_series.index <= season_end)
        )

        mean_temp = temp_series.loc[temp_mask].mean()
        mean_precip = precip_series.loc[precip_mask].mean()

        print(
            year,
            "dry-season mean temperature =",
            mean_temp,
            "mean precipitation =",
            mean_precip
        )

        # Mean temperature
        if pandas.notna(mean_temp):

            temp_ax.hlines(
                y=mean_temp,
                xmin=season_start,
                xmax=season_end,
                colors=temp_color,
                linewidth=linewidth,
                zorder=10
            )

            if annotate:
                temp_ax.text(
                    season_middle,
                    mean_temp + 0.3,
                    f"{mean_temp:.1f}°C",
                    color="black",#temp_color,
                    ha="center",
                    va="bottom",
                    fontsize=9
                )

        # Mean daily precipitation
        if pandas.notna(mean_precip):

            precip_ax.hlines(
                y=mean_precip,
                xmin=season_start,
                xmax=season_end,
                colors=precip_color,
                linewidth=linewidth,
                zorder=10
            )

            if annotate:
                precip_ax.text(
                    season_middle,
                    mean_precip,
                    f"{mean_precip:.1f} mm/d",
                    color=precip_color,
                    ha="center",
                    va="bottom",
                    fontsize=9
                )

def plot_longest_dry_spells(
    my_start_date,
    my_end_date,
    dates,
    precipitations,
    precip_ax,
    dry_threshold=1.0,
    y_position=3.0,
    my_color="black",
    linewidth=3.0,
    annotate=True
):
    """
    For each dry season, find the longest consecutive run of days
    with precipitation < dry_threshold, and draw a horizontal line
    spanning that interval.

    Parameters
    ----------
    dry_threshold : float
        Daily precipitation below this value counts as a dry day.
        Default = 1.0 mm/day.

    y_position : float
        Vertical position of the line on the precipitation axis.
    """

    start_year = pandas.to_datetime(my_start_date).year
    end_year   = pandas.to_datetime(my_end_date).year

    weather = pandas.DataFrame({
        "date": pandas.to_datetime(dates),
        "precip": precipitations
    }).sort_values("date")

    for year in range(start_year, end_year + 1):
        season_start, season_end = get_warm_dry_season(year)
        year_offset = 2025 - year


        season = weather.loc[
            (weather["date"] >= season_start)
            & (weather["date"] <= season_end)
        ].copy()

        if season.empty:
            continue

        #season["dry"] = season["precip"].fillna(0) < dry_threshold


        season["dry"] = (
            season["precip"].notna()
            & (season["precip"] < dry_threshold)
        )

        longest_start = None
        longest_end = None
        longest_length = 0

        current_start = None
        current_length = 0

        for _, row in season.iterrows():

            if row["dry"]:

                if current_start is None:
                    current_start = row["date"]

                current_length += 1

                if current_length > longest_length:
                    longest_length = current_length
                    longest_start = current_start
                    longest_end = row["date"]

            else:
                current_start = None
                current_length = 0

        if longest_start is None:
            continue

        precip_ax.hlines(
            y=y_position,
            xmin=longest_start,
            xmax=longest_end,
            color=my_color,
            linewidth=linewidth,
            zorder=20
        )

        if annotate:

            middle = longest_start + (longest_end - longest_start) / 2

            precip_ax.text(
                middle,
                y_position + 1.5,
                f"{longest_length} d",
                color=my_color,
                ha="center",
                va="bottom",
                fontsize=9
            )

        print(
            year,
            "longest dry spell:",
            longest_length,
            "days,",
            longest_start.date(),
            "to",
            longest_end.date()
        )
