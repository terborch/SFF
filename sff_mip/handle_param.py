"""
### Methods for reading and calculating a few recurrent parameters
    #   TODO. list methods
"""

# External modules
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Internal modules
import data


def print_error(error):
    switcher = { 
        'Time_step' : 'Time_step has to be either a number of hours or a nuber of minutes',
        'Time_step_int' : 'Time_step is not an integer number'
    }
    message = switcher.get(error, 'unspecified error')
    
    print('########################## INPUT ERROR ##########################')
    print(message)
    print('########################## INPUT ERROR ##########################')
    

def get_values_df(file):
    """ Get data from a csv file and return a datafram. Convert every 'Value' entry into a float
        except for entries in the cathegory 'Time'
    """
    df = data.open_csv(file, 'inputs', ',')
    
    for i in df.index:
        if df['Category'][i] != 'Time' and type(df['Value'][i]) != np.float64:
            df['Value'][i] = float(df['Value'][i])
    
    return df
    

def get_settings(file):
    """ Get values and metadata from csv settings files in this directory and store them 
        into separate dictionaries 
    """
    df = get_values_df(file)
    
    df.index = df['Name']
    dic_value = df.to_dict()
    
    dic_meta = {}
    for n in df.index:
        meta = []
        for c in df.columns:
            if c != 'Name':
                meta.append(df[c][n])
            else:
                name = df['Name'][n]
        dic_meta[name] = meta
     
    return dic_value['Value'], dic_meta


def get_param(file):
    """ Get values and metadata from csv parameter files in this directory and 
        store them into separate dictionaries.
    """
    df = get_values_df(file)
    dic, dic_meta = {}, {}
    Categories = set(df['Category'].values)
    for c in Categories:
        dic[c] = {}
        dic_meta[c] = {}
    for i in df.index:
        meta = []
        for col in ['Units', 'Description', 'Source']:
                meta.append(df[col][i])
        dic_meta[df['Category'][i]][df['Name'][i]] = meta
        dic[df['Category'][i]][df['Name'][i]] = df['Value'][i]
     
    return dic, dic_meta, Categories
        

def time_param(S):
    """ Return the list of Periods, the number of Nbr_of_time_steps and the duration of the each
        time step dt, based on the given Time informations in the settings.csv file. The 
        units are in hours. Adds their value and metadata to P and P_meta.
    """
    # dt
    dt = datetime.strptime(S['Time_step'], S['Time_format']).time()
    if dt.hour != 0 and dt.minute == 0 and dt.second == 0:
        dt = dt.hour
    elif dt.hour == 0 and dt.minute != 0 and dt.second == 0:
        dt = dt.minute / 60
    else:
        print_error('Period_length')
    
    Datetime_format = S['Date_format'] + ' ' + S['Time_format']
    start = S['Period_start'] + ' ' + S['Period_start_time']
    dt_start = datetime.strptime(start, Datetime_format)
    end = S['Period_end'] + ' ' + S['Period_start_time']
    dt_end = datetime.strptime(end, Datetime_format)
    
    # Nbr_of_time_steps
    Nbr_of_time_steps = ((dt_end - dt_start).days * 24) / dt
    Nbr_of_time_steps_per_day = 24 / dt
    
    # Period index
    if int(Nbr_of_time_steps) == Nbr_of_time_steps and int(Nbr_of_time_steps_per_day) == Nbr_of_time_steps_per_day:
        Periods = list(range(0, int(Nbr_of_time_steps)))
    else:
        print_error('time_step_int')
    
    # Day index
    Days = list(range((dt_end - dt_start).days))
    
    # Hour index
    Hours = list(range(0,24))
    
    # Date of each day
    Day_dates = [dt_end - timedelta(days=i) for i in range(len(Days))]

    Time = []
    for t in range(0, int(Nbr_of_time_steps_per_day)):
        Time.append(datetime.strftime(Day_dates[0] + timedelta(hours=t*dt), S['Time_format']))   
    
    return Periods, Nbr_of_time_steps, dt, Day_dates, Time, dt_end, Days, Hours


def annualize(n, i):
    """ Takes the number of years and interest rate as parameters and returns 
        the annualization factor Tau
    """
    return (i*(1 + i)**n) / ((1 + i)**n - 1)




