""" This module contains all functions necessary get data out of the 'model_data'
    folder and into useable dataframes. The two key functions are:
    weather_data_to_df(file, period_start, period_end, timestep)
    default_data_to_df(file, df_index=None)
    
    #   TODO: add a way to calculate typical days
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import os.path



##################################################################################################
### External Parameter (weather profiles)
##################################################################################################


def open_csv(file, folder, separator):
    """ Open a csv file in a inputs subfolder given a file name, a folder and a separator. """
    if folder != 'inputs':
        path = os.path.join('inputs', folder, file)
    else:
        path = os.path.join('inputs', file)
    return pd.read_csv(path , sep = separator, engine='python')
 

def to_date_time(df, column):
    """ Convert a dataframe column to datetime and set it as index. """
    df[[column]] = pd.DataFrame(pd.to_datetime(df[column], format='%d.%m.%Y %H:%M'))
    df.set_index(column, inplace = True)


def time_delta(delta):
    """ Get a timedelta object from a given string with a fomat hrs_min_sec as "00:00:00" hours 
        minutes seconds.
    """
    t = datetime.strptime(delta,"%H:%M:%S")
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)


def weather_data_to_df(file, period_start, period_end, timestep):
    """ Create a dataframe from a csv file of meteorological data for a given period and with a 
        given timestep
    """
    folder = 'external'
    df = open_csv(file, folder, ';')
    to_date_time(df, 'Date')
    
    df = df.truncate(before = period_start, after = period_end)
    
    # Sum over Irradiance values: units of Irradiance are now kWh/m^2/h = kW/m^2
    df = df.resample(time_delta(timestep)).agg({'Irradiance': np.sum, 'Temperature': np.mean})
    df['Irradiance'] /= 1000 
    return df



##################################################################################################
### Internal Parameters (consumption profiles)
##################################################################################################


def rename_csv(df):
    """ Remove the wonky characters from the first column's name typical for hand made csv files
    """
    name = df.columns[0].split('¿')[1]
    df.rename(columns={df.columns[0] : name}, inplace = True)


def default_data_to_df(file, folder, df_index=None):
    """ Open a hand made csv file. Rename its first column. Either set a given timestep as index 
        or a given column.
    """
    df = open_csv(file, folder, ',')
    
    if df.columns[0][0] == 'ï':
        rename_csv(df)
    
    if type(df_index) == pd.core.indexes.range.RangeIndex:
        df.set_index(df_index, inplace = True)
        
    elif type(df_index) == int:
        df.set_index(df.columns[df_index], inplace = True)
        
    return df



##################################################################################################
### Display input data
##################################################################################################
    

def display_inputs(S, Disp_cons):
    
    plt.rcParams['figure.figsize'] = [15, 5]
    period_start = S['Period_start'] + ' ' + S['Period_start_time']
    period_end = S['Period_end'] + ' ' + S['Period_start_time']
    timestep = S['Time_step']
    file = 'meteo_Liebensberg_10min.csv'
    
    df_weather = weather_data_to_df(file, period_start, period_end, timestep)
    
    time = df_weather.index
    irr = df_weather['Irradiance']
    temp = df_weather['Temperature']
    
    fig, ax1 = plt.subplots()
    
    c = 'red'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Irradiance in kW')
    ax1.plot(time, irr, color=c)
    ax1.tick_params(axis='y', labelcolor=c)
    fig.autofmt_xdate()
    
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    
    c = 'blue'
    ax2.set_ylabel('Temperature in °C')  # we already handled the x-label with ax1
    ax2.plot(time, temp, color=c)
    ax2.tick_params(axis='y', labelcolor=c)
    
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.title('Weather data for Liebensberg from ' + S['Period_start']  + 'to' + S['Period_end'])
    
    return plt
    
    if Disp_cons:
        # get a user made csv file into a dataframe
        file = 'Consumption_profile_dummy.csv'
        folder = 'internal'
        df_cons = default_data_to_df(file, folder, df_weather.index)
        
        # Plot daily profiles as a function of time
        df_cons.plot()
        plt.title('Daily consumption and internal gains profiles')
        plt.show()
