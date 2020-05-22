""" This module contains all functions necessary get data out of the 'model_data'
    folder and into useable dataframes. The two key functions are:
    weather_data_to_df(file, period_start, period_end, timestep)
    default_data_to_df(file, df_index=None)
    
    #   TODO: add a way to calculate typical days and extreme days and their position
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import os.path
import json


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
### Load weather clustering results and sorting algorythm
##################################################################################################
    

def read_json(file_path):
    """ Import 'labels' and 'closest' values from a json file """
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
    return data['labels'], data['closest']

def unique(l):
    """ Return a list of unique elements from a given list and change them into 
        ints 
    """
    return list(set([int(i) for i in l]))

def reorder(a, order):
    """ Reorder the array a according to the order array """
    ordered = np.zeros(len(order))
    for i in range(len(order)):
        ordered[i] = a[order[i]]
    return ordered
    
def get_frequence(Labels):
    """ Returns the number of occurances for each cluster """
    frequence = np.zeros(len(unique(Labels)))
    for i in unique(Labels):
        frequence[i] = Labels.count(i)
    if sum(frequence) == len(Labels):
        return frequence
    else:
        print('The sum of clusters of days is not 365')

def get_nearby(start, stop, Labels):
    """ Cycle through a list representing a year. Returns a splice between a
        start and a stop index. 
    """
    if start >= 0 and stop <= len(Labels):
        return Labels[start:stop]
    else:
        if start <= 0:
            return Labels[len(Labels) + start:-1] + Labels[0:stop]
        else:
            return Labels[start:-1] + Labels[0:stop - len(Labels)]

def filter_labels(Labels, initial_distance):
    """ Runs a simple nearest neighboors type filter on the 1D array Labels.
        Finds the largest filtering distance such that at least one of each
        cluster appeary in a year, by iteration. Returns the filtered labels.
    """
    Filtered_labels = [0]
    distance = initial_distance
    while len(unique(Filtered_labels)) != len(unique(Labels)):
        count_near_day = {}
        for d in range(len(Labels)):
            count_near_day[d] = {}
            nearby = get_nearby(d - distance, d + distance, Labels)
            for p in unique(nearby):
                c = nearby.count(p)
                count_near_day[d][p] = c
                
        Filtered_labels = np.zeros(len(Labels))
        for d in range(len(Labels)):
            index = np.argmax(list(count_near_day[d].values()))
            Filtered_labels[d] = list(count_near_day[d].keys())[index]
        
        distance -= 1

    return Filtered_labels

def reduce_reorder(Labels, cluster):
    """ Given a list of labels and a specific cluster to place and cut it looks
        for the longest uninterupted occurence of that cluster and replace it
        by a signle int of the cluster. 
        All other occurences of the cluster are cut. 
        The reduced list of labels is returned. 
    """
    period_occure = np.where(np.array(Labels) == cluster)[0]
    length = {}
    i, j = 0, period_occure[0]
    for n, _ in enumerate(period_occure):
        try:
            if period_occure[n + 1] == period_occure[n] + 1:
                i += 1
            else:
                length[j] = i + 1
                i, j = 0, period_occure[n+1]
        except:
            length[j] = i + 1
            
    key_max = max(length, key=length.get)
    for k in list(length.keys())[::-1]:
        l = length[k]
        if k == key_max:
            Labels[k:k+l] = [cluster]
        else:
            Labels[k:k+l] = []
    return Labels

def arrange_clusters(Labels, display=False):
    """ Orders clusters of typical days accurding to a liste of cluster labels.
        Starting by the least frequently appearing cluster, this cluster value
        is cut from Labels list. 
        The longest uninterupted chain of days in that cluster is replaced by a 
        signle value.
        Once each clsuter has been cut a list of ordered clusters is returned.
    """
    Filtered_labels = filter_labels(Labels, len(unique(Labels)))
    
    frequency = []
    for i in unique(Filtered_labels):
        frequency.append(np.count_nonzero(Filtered_labels == i))
    frequency = [unique(Filtered_labels), frequency]
    
    Ordered_labels = list(Filtered_labels)
    for i in unique(Ordered_labels):
        smallest = frequency[0].pop(np.argmin(frequency[1]))
        frequency[1].pop(np.argmin(frequency[1]))
        if display:
            print('---------- Least frequent cluster: ', smallest, '--------')
            print('Remaining elements of the least frequent cluster to be cut', 
                  np.count_nonzero(np.array(Ordered_labels) == smallest))
            print(Ordered_labels)
        Ordered_labels = reduce_reorder(list(Ordered_labels), smallest)
        if display:
            print('Remaining elements of the least frequent cluster after cut', 
                  np.count_nonzero(np.array(Ordered_labels) == smallest))
    return Ordered_labels



##################################################################################################
### END --- Unused functions
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
