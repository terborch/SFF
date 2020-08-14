""" This module contains all functions necessary get data out of the 'inputs'
    folder and into useable dataframes. As well as other data handeling 
    functions used by all other modules.
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import os.path
import json

 

###############################################################################
### Read and Write from files
###############################################################################


def save_to_hdf(key, item, path):
    """ Save an 'item' to a hdf5 file format using pandas. Print the location. 
    """
    df = pd.DataFrame(item)
    with pd.HDFStore(path) as hdf:
        hdf.put(key, df)
    print(f'Item {key} saved to {path}')
    
    
def get_hdf(file_path, *args, Series=False):
    """ Fetch all items stored in a hdf file and returns a dictionnary. 
        If args are passed only opens the items in args.
    """
    result_dic = {}
    with pd.HDFStore(file_path) as hdf:
        if not args:
            for i in hdf.keys():
                result_dic[i[1:]] = hdf[i]
        elif len(args) > 1:
            for i in args:
                result_dic[i] = hdf[i]
        else:
            result_dic = hdf[args[0]]
    if Series:
        for k in result_dic.keys():
            result_dic[k] = result_dic[k].values.T[0]
    return result_dic


def open_csv(file, folder, separator):
    """ Open a csv file in a inputs subfolder given a file name, a folder and a separator. """
    if folder != 'inputs':
        path = os.path.join('inputs', folder, file)
    else:
        path = os.path.join('inputs', file)
    return pd.read_csv(path , sep = separator, engine='python')


def read_json(file_path):
    """ Import clustering values from a json file """
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
    return data['labels'], data['closest']


def get_all_param():
    """ Get all parameters in values series and df metadata """
    P, P_meta = get_param('parameters.csv')
    P_calc, P_meta_calc = get_param('calc_param.csv')
    P_eco, P_meta_eco = get_param('cost_param.csv')
    P, P_meta = P.append(P_calc), P_meta.append(P_meta_calc)
    P, P_meta = P.append(P_eco), P_meta.append(P_meta_eco)
    return P, P_meta


###############################################################################
### External Parameter (weather profiles)
###############################################################################
 

def to_date_time(df, column, dt_format='%d.%m.%Y %H:%M'):
    """ Convert a dataframe column to datetime and set it as index. """
    df[[column]] = pd.DataFrame(pd.to_datetime(df[column], format=dt_format))
    df.set_index(column, inplace = True)


def time_delta(delta):
    """ Get a timedelta object from a given string with a fomat hrs_min_sec as "00:00:00" hours 
        minutes seconds.
    """
    try:
        t = datetime.strptime(delta,"%H:%M:%S")
    except:
        return timedelta(days=delta)
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)


def weather_data_to_df(file, period_start, period_end, timestep):
    """ Create a dataframe from a csv file of meteorological data for a given period and with a 
        given timestep
    """
    folder = 'profiles'
    subfolder = 'weather'
    df = open_csv(file, os.path.join(folder, subfolder), ',')
    for t in ['Temperature', 'Irradiance']:
        df[t] = pd.to_numeric(df[t], errors='coerce')
        
    to_date_time(df, 'Date')
    
    df = df.truncate(before = period_start, after = period_end)
    
    # Sum over Irradiance values: units of Irradiance are now kWh/m^2/h = kW/m^2
    df = df.resample(time_delta(timestep)).agg({'Irradiance': np.sum, 'Temperature': np.mean})
    df['Irradiance'] /= 1000 
    return df


def extreme_day(file, S):
    # Add coldest day in the 10 last year
    file = 'meteo_Liebensberg_10years.csv'
    df = weather_data_to_df(file, '2010-01-01', '2020-01-01', S['Time_step'])
    Daily_sum = df.resample(time_delta(1)).agg({'Temperature': np.mean, 
                                                'Irradiance': np.sum})
    Minima = Daily_sum['Temperature'].idxmin().strftime(S['Date_format'])
    return df.loc[Minima]


###############################################################################
### Internal Parameters (consumption profiles)
###############################################################################


def print_error(error):
    """ Error message for poorly formatted inputs """
    switcher = { 
        'Time_step' : '''Time_step has to be either a number of hours or a nuber 
                       of minutes''',
        'Time_step_int' : 'Time_step is not an integer number',
        'calc_param' : '''The written data to calc_param.csv is not the same 
                            shape as the existing data'''
    }
    message = switcher.get(error, 'unspecified error')
    
    print('########################## INPUT ERROR ##########################')
    print(message)
    print('########################## INPUT ERROR ##########################')


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
    

def csv_to_df(file):
    """ Get data from a csv file and return a datafram. Convert every 'Value' 
        entry into a float except for entries in the cathegory 'Time' and 
        'Profile'.
    """
    df = open_csv(file, 'inputs', ',')

    return df


def df_to_series(df):
    """ Index a given dataframe by 'Category' and 'Name' then return a series
        of values and a dataframe of metadata without values.
    """
    df.set_index(['Category', 'Name'], inplace=True)
    
    return df['Value'], df.drop(columns=['Value'])


def get_param(file):
    """ Return value series and metadata dataframe for a given csv file name 
        in the inputs folder.
    """
    df = csv_to_df(file)
    
    df['Units'] = df['Units'].str.replace('Â','')
    
    for i in df.index:
        if df.loc[i, 'Category'] not in ['Profile', 'Time']:
            try:
                df.loc[i, 'Value'] = pd.to_numeric(df.loc[i, 'Value'])
            except ValueError:
                pass
    
    Series, Meta_df = df_to_series(df)
    
    return Series, Meta_df


def get_profile(file):
    """ Return an array of a profile  """
    df = open_csv(file, 'profiles', ',')
    
    return df[df.columns[0]].values

        
def make_param(category, name, value, meta):
    """ Create a new parameter and add it to the calc_param.csv file 
        Option to pass a list of names, a series of values and a dict of
        metadata, but only for one category.
    """
    
    # Open the calculated parameter csv file as dataframe and set index
    df = csv_to_df('calc_param.csv')
    df.set_index(['Category', 'Name'], inplace=True)
    
    # Either recieve a signle name and store it with its metadata
    data = {}
    if type(name) == str:
        data[name] = [value] + meta
        
    # Or store a list of names with a set of matching values and metadata
    elif type(name) == list:
        for n in name:
            data[n] = [value[category, n]] + meta[n]
    
    # Add new values to the dataframe
    columns = ['Value', 'Units', 'Description', 'Source']
    for n in data:
        df.loc[(category, n), columns] = data[n]
        if len(df.columns) != len(data[n]):
            print_error
            
    # Save the new dataframe in csv format
    df.sort_values(['Category', 'Name'], inplace=True)
    df.to_csv(os.path.join('inputs', 'calc_param.csv'))
    return


def change_settings(category, name, value, file='settings.csv'):
    """ Modify an existing setting value by name and category """
    
    # Open the settings.csv file as dataframe and set index
    df = csv_to_df(file)
    df.set_index(['Category', 'Name'], inplace=True)
    
    # Change the selected values
    df.loc[(category, name), 'Value'] = value
            
    # Save the new dataframe in csv format
    df.to_csv(os.path.join('inputs', file))
    return


def reset_settings():
    """ Reset the settings file to the default version in the unused folder """
    df = csv_to_df(os.path.join('unused', 'settings.csv'))
    df.set_index(['Category', 'Name'], inplace=True)
    df.to_csv(os.path.join('inputs', 'settings.csv'))
    return

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
    Nbr_of_time_steps = (((dt_end - dt_start).days + 1) * 24) / dt
    Nbr_of_time_steps_per_day = 24 / dt
    
    # Period index
    if (int(Nbr_of_time_steps) == Nbr_of_time_steps and 
        int(Nbr_of_time_steps_per_day) == Nbr_of_time_steps_per_day):
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
        Refernce in the report: eq. (82)
    """
    return (i*(1 + i)**n) / ((1 + i)**n - 1)


def annual_to_daily(Annual, Profile_norm):
    """ Take an annual total and a corresponding daily profile normalized from 1 to 0. Calculate 
        the average instant, then the average of the normalized profile, then the corresponding
        peak value. It returns the product of the peak and normalized profile, i.e. the
        actual profile or instanteneous load.
    """
    Average = Annual / 8760
    Average_profile_norm = float(np.mean(Profile_norm))
    Peak = Average / Average_profile_norm

    return np.array(Peak * Profile_norm)



###############################################################################
### Load weather clustering results and sorting algorythm
###############################################################################


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
    # Filtered_labels = filter_labels(Labels, len(unique(Labels)))
    Filtered_labels = Labels
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


def reshape_day_hour(hourly_indexed_list, Days_all, Hours):
    """ Reshape a list with hourly index to a list of list with daily and hour 
    in day index """
    return (np.reshape(hourly_indexed_list, (len(Days_all), len(Hours))))


def cluster(a, Clustered_days, Hours):
    clustered_a = np.zeros((len(Clustered_days), len(Hours)))
    for i, c in enumerate(Clustered_days):
        clustered_a[i] = a[int(c)]
    return clustered_a


def weather_param(file, epsilon, Format, S):
    """ Returns Ext_T and Irradiance where values within epsilon around zero
        will be replaced by zero. Format is a tuple with two lists first the
        Days then the Hours.
    """
    df_weather = weather_data_to_df(file, S['Period_start'], S['Period_end'], S['Time_step'])
    df_weather.drop(df_weather.tail(1).index, inplace=True)
    
    # External temperature - format Ext_T[Day_index,Hour_index]
    Ext_T = reshape_day_hour((df_weather['Temperature'].values), *Format)
    Ext_T[np.abs(Ext_T) < epsilon] = 0
    
    # Global irradiance
    Irradiance = reshape_day_hour((df_weather['Irradiance'].values), *Format)
    Irradiance[np.abs(Irradiance) < epsilon] = 0
    
    return Ext_T, Irradiance, df_weather.index

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
    plt.title('Weather data for Liebensberg from ' + S['Period_start']  + ' to ' + S['Period_end'])
    
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






# def get_settings(file):
#     """ Get values and metadata from csv settings files in this directory and store them 
#         into separate dictionaries 
#     """
#     df = get_values_df(file)
    
#     df.index = df['Name']
#     dic_value = df.to_dict()
    
#     dic_meta = {}
#     for n in df.index:
#         meta = []
#         for c in df.columns:
#             if c != 'Name':
#                 meta.append(df[c][n])
#             else:
#                 name = df['Name'][n]
#         print(name, meta)
#         dic_meta[name] = meta
     
#     return dic_value['Value'], dic_meta


# def get_param(file):
#     """ Get values and metadata from csv parameter files in this directory and 
#         store them into separate dictionaries.
#     """
#     df = get_values_df(file)
#     dic, dic_meta = {}, {}
#     Categories = set(df['Category'].values)
#     for c in Categories:
#         dic[c] = {}
#         dic_meta[c] = {}
#     for i in df.index:
#         meta = []
#         for col in ['Units', 'Description', 'Source']:
#                 meta.append(df[col][i])
#         dic_meta[df['Category'][i]][df['Name'][i]] = meta
#         dic[df['Category'][i]][df['Name'][i]] = df['Value'][i]
     
#     return dic, dic_meta, Categories