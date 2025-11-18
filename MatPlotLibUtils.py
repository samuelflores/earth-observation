import importlib
import numpy as np 
import pandas 
importlib.reload(pandas)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import inspect
import Constants

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
        SSEDA.insert(0,
            (Constants.warmDryStart2025 - pandas.DateOffset(years = endYear-year),  #season start
             Constants.warmDryEnd2025   - pandas.DateOffset(years = endYear-year),  #season end 
             Constants.warmDryStart2025 - pandas.DateOffset(years = endYear-year) + (Constants.warmDryEnd2025 - Constants.warmDryStart2025)/2 #season middle
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


def indicate_seasons_box(my_start_date,my_end_date, my_ax,my_label="Dry season",my_color="black",line_style="solid"):   
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
        SSEDA.insert(0,
            (Constants.warmDryStart2025 - pandas.DateOffset(years = endYear-year),  #season start
             Constants.warmDryEnd2025   - pandas.DateOffset(years = endYear-year),  #season end 
             Constants.warmDryStart2025 - pandas.DateOffset(years = endYear-year) + (Constants.warmDryEnd2025 - Constants.warmDryStart2025)/2 #season middle
        ))
        # draw a line across the interval at 90% height of NDMI axis
        my_ax.hlines(y=27  , xmin=SSEDA[0][0], xmax=SSEDA[0][1], color=my_color, lw=1.2)
        # put label slightly above the line
        my_ax.text(SSEDA[0][2],28 , my_label, ha="center", va="bottom", fontsize=9)
