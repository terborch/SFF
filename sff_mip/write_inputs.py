"""
### Read or calculate all parameters then write them to the inputs files
    # Write the dictionnary P for signle value parameters to inputs.csv 
    # Write each parameter array to inputs.h5 with its name as key
"""

"""
### Get input parameters and settings. Define time related parameters. 
    #   P       dict with parameters values from parameters.csv will contain calculated parameters
                P has at least two entries, the first is the Category and the second is the
                parameter name or sub-category. Categories is a list of Category names.
    #   S       dict with settings values from settings.csv
    #   P_meta  dict tracking the metadata of model parameters
    #   S_meta  dict tracking the metadata of model settings
    #   V_meta  dict tracking the metadata of model variables
    #   C_meta  dict tracking the metadata of model constraints
    #   Bound       the upped bound of most variables
    #   Periods     list of time period indexes
    #   Nbr_of_time_steps  the number of timesteps
    #   dt          the duration of a time step in hours
    #   Days        list of days in a date format '2019-01-01'
    #   Time        list of hours in a day in a time format '12:00:00'
    #   make_param  function passing values and metadata of a parameter into P and P_meta
"""

# External modules
import numpy as np
import pandas as pd
from datetime import datetime
import os
# Internal modules
import data

from handle_param import get_param, get_settings, time_param



def make_param(category, name, value, meta, *subcategory):
    """ Passes the value and metadata of a given parameter into P and P_meta, 
        given a Category and a name.
    """   
    if not subcategory:
        P[category][name] = value
        P_meta[category][name] = meta
    else:
        subcategory  = subcategory[0]
        try:
            P[category][subcategory][name] = value
        except KeyError:
            P[category][subcategory], P_meta[category][subcategory] = {}, {}
            P[category][subcategory][name] = value
        
        P_meta[category][subcategory][name] = meta        

###############################################################################
### Functions specific to ......................
###############################################################################

# Dictionnaries of values and metadata from the file 'parameters.csv'
# example: P['AD']['eff'] = 0.3 and P_meta['AD']['eff'] = ['-', 'AD efficiency', 'energyscope']
P, P_meta, Categories = get_param('parameters.csv')
# Dictionnaries of values and metadata from the file 'Settings.csv'
S, S_meta = get_settings('settings.csv')
# Dictionnary describing each constraint and its source if applicable
C_meta = {}
# Dictionnary of parameters to be stored in hdf5 format
P_dict = {}
# Time discretization

def typical_days(Periods, Hours, Cluster=True, Identifier=6, Number_of_clusters=12):

    path = os.path.join('jupyter_notebooks', 'jsons', 
                        f'clusters_{Identifier}_{Number_of_clusters}.json')
    Labels, Closest = [r[f'{Number_of_clusters}'] for r in data.read_json(path)]
    Clusters_order = data.arrange_clusters(Labels)
    Clustered_days = data.reorder(Closest, Clusters_order)
    Frequence = data.get_frequence(Labels)
    Frequence = data.reorder(Frequence, Clusters_order)
    
    if not Cluster:
        Labels = list(range(365))
        Closest = list(range(365))
        Clustered_days = list(range(365))
        Days = list(range(365))
        Frequence = [1]*365

    Days = list(range(len(Clustered_days)))

    # Map each time period p to a corresponding day-hour pair
    Time_period_map = np.zeros((len(Periods), 2))
    p = 0
    for d in Days:
        for f in range(int(Frequence[d])):
            for h in Hours:
                Time_period_map[p] = [d,h]
                p += 1
            
    return Days, Frequence, Time_period_map, Clustered_days

          

def save_to_hdf(key, item, path):
    df = pd.DataFrame(item)
    with pd.HDFStore(path) as hdf:
        hdf.put(key, df)
    print(f'Item {key} saved to {path}')






###############################################################################
###############################################################################



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


def biomass_prod(Pigs, Cows):
    """ Given an number of cows and pigs, calculate the biomass potential in kW"""
    
    c = 'AD'
    LSU = Pigs*P[c]['LSU_pigs'] + Cows
    make_param(c, 'LSU', LSU, ['LSU', 'Number of LSU', 'calc'])
    
    P_meta[c]['Manure_prod'] = ['kW', 'Manure Production', 'calc']
    C_meta['Manure_prod'] = ['Production of manue relative to the number of LSU', 1, 'P']
    P[c]['Manure_prod'] = LSU*P[c]['Manure_per_cattle']*P[c]['Manure_HHV_dry']/24
    
    return P[c]['Manure_prod']


def AD_dimentions(P, P_meta):
    """ Given a number of LSU and a Hydrolic Residence Time (HTR) defined in the parameter.csv 
        file estimate the AD cylindrical body volume and add it as a parameter.
        Then given dimention ratios, the cap surface area is calculated. Similarly the cap height,
        body height and body diameter are calculated and stored.
    """
    c = 'AD'
    name = 'Sludge_volume'
    P_meta[c][name] = ['m^3', 'Sludge volume capacity', 'calc']
    P[c][name] = np.ceil( P[c]['Residence_time']*P[c]['LSU']*P[c]['Manure_per_cattle']/
                       (1 - P[c]['Biomass_water'])/1000 )
    
    name = 'Cyl_volume'
    P_meta[c][name] = ['m^3', 'Cylinder volume', 'calc']
    P[c][name] = np.ceil( P[c]['Sludge_volume']/P[c]['Cyl_fill'] )

    name = 'Cap_height'
    P_meta[c][name] = ['m', 'Height of the AD top cap', 'calc']
    P[c][name] = np.round( (P[c]['Sludge_volume']*P[c]['Cap_V_ratio']*(6/np.pi)/
                         (3*P[c]['Cap_h_ratio']**2 + 1))**(1/3), 2)
    
    name = 'Diameter'
    P_meta[c][name] = ['m', 'Diameter of the AD cylindrical body', 'calc']
    P[c][name] = np.round( P[c]['Cap_h_ratio']*P[c]['Cap_height']*2, 2)
    
    name = 'Ground_area'
    P_meta[c][name] = ['m^2', 'Ground floor area', 'calc']
    P[c][name] = np.round( np.pi*P[c]['Diameter']**2, 2)
    
    name = 'Cap_area'
    P_meta[c][name] = ['m^2', 'Surface area of the AD top cap', 'calc']
    P[c][name] = np.round( np.pi*(P[c]['Cap_height']**2 + (P[c]['Diameter']/2)**2), 2)
    
    name = 'Cyl_height'
    P_meta[c][name] = ['m', 'Height of the AD cylindrical body', 'calc']
    P[c][name] = np.round( P[c]['Cyl_volume']/(np.pi*(P[c]['Diameter']/2)**2), 2)



def reshape_day_hour(hourly_indexed_list, Days_all, Hours):
    """ Reshape a list with hourly index to a list of list with daily and hour 
    in day index """
    return (np.reshape(hourly_indexed_list, (len(Days_all), len(Hours))))


def cluster(a, Clustered_days, Hours):
    clustered_a = np.zeros((len(Clustered_days), len(Hours)))
    for i, c in enumerate(Clustered_days):
        clustered_a[i] = a[int(c)]
    return clustered_a


def weather_param(file, epsilon, Days_all, Hours, Clustered_days, clustering=True):
    """ Returns Ext_T and Irradiance where values within epsilon around zero
        will be replaced by zero.
    """
    df_weather = data.weather_data_to_df(file, S['Period_start'], S['Period_end'], S['Time_step'])
    df_weather.drop(df_weather.tail(1).index, inplace=True)
    
    # External temperature - format Ext_T[Day_index,Hour_index]
    Ext_T = reshape_day_hour((df_weather['Temperature'].values), Days_all, Hours)
    Ext_T[np.abs(Ext_T) < epsilon] = 0
    P_meta['Timedep']['Ext_T'] = ['°C', 'Exterior temperature', 'agrometeo.ch']
    
    # Global irradiance
    Irradiance = reshape_day_hour((df_weather['Irradiance'].values), Days_all, Hours)
    Irradiance[np.abs(Irradiance) < epsilon] = 0
    P_meta['Timedep']['Irradiance'] = ['kW/m^2', 'Global irradiance', 'agrometeo.ch']
    
    # Clustering
    if clustering:
        Ext_T = cluster(Ext_T, Clustered_days)
        Irradiance = cluster(Irradiance, Clustered_days)
    
    return Ext_T, Irradiance, df_weather.index






def write_inputs(path, Cluster=True):
    # List of periods, number of time steps and delta t (duration of a time step) in hours
    Periods, Nbr_of_time_steps, dt, Day_dates, Time, dt_end, Days_all, Hours = time_param(S)
    
    Days, Frequence, Time_period_map, Clustered_days = typical_days(Periods, Hours, Cluster=Cluster) 
    
    P_dict['Frequence'] = Frequence
    P_dict['Time_period_map'] = Time_period_map
    P_dict['Days'] = Days
    
    
    
    # Hoourly weather parameters for a year at Liebensberg
    filename = 'meteo_Liebensberg_10min.csv'
    epsilon = 1e-6
    Ext_T, Irradiance, Index = weather_param(filename, epsilon, Days_all, Hours, Clustered_days, clustering=True)
    
    # List of dates modelled
    Dates, Dates_pd = [], Index
    for d in Dates_pd: 
        Dates.append(datetime.datetime(d.year, d.month, d.day, d.hour, d.minute))
    
    # Daily building electricity consumption profile
    Build_cons = {}
    meta = ['kW', 'Building electricity consumption', 'calc']
    file = 'consumption_profile_dummy.csv'
    df_cons = data.default_data_to_df(file, 'internal', Index)
    Build_cons['Elec'] = annual_to_daily(P['build']['cons_Elec_annual'], df_cons['Electricity'].values)
    make_param('Timedep', 'Build_cons[Elec]', Build_cons['Elec'], meta)
    
    # Biomass potential
    Biomass_prod = biomass_prod(P['AD']['Pigs'], P['AD']['Cows'])
    make_param('AD', 'Biomass_prod', Biomass_prod, ['kW', 'Biomass production', 'calc'])
    
    # Building heated surface area and ground floor area
    file = 'buildings.csv'
    df_buildings = data.default_data_to_df(file, 'inputs', 0)
    Heated_area, Ground_area = 0, 0
    for i in df_buildings.index:
        Heated_area += (df_buildings['Ground_surface'][i] * df_buildings['Floors'][i])
        Ground_area += df_buildings['Ground_surface'][i]
    meta = ['m^2', 'Building heated surface area', 'Building']
    make_param('build', 'Heated_area', Heated_area, meta)
    meta = ['m^2', 'Building ground surface area', 'Building']
    make_param('build', 'Ground_area', Ground_area, meta)
    


    P_dict['Ext_T'] = Ext_T
    P_dict['Irradiance'] = Irradiance
    P_dict['Build_cons[Elec]'] = Build_cons['Elec']


    for k in P_dict.keys():
        save_to_hdf(k, P_dict[k], path)  





