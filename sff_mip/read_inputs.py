import os

from write_inputs import get_param, get_settings, time_param
import results


# External modules
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Internal modules
import data
from global_set import Units

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



def unit_economics(file):
    """ Given a file name, return a dataframe of unit costs from the data forlder """
    df = data.default_data_to_df(file, 'economic', 0)
    
    # Convert strings of valuesto numpy.int64
    Parameters = ['Cost_per_size', 'Cost_per_unit', 'Cost_multiplier', 'Life']
    Descriptions = {'Cost_per_size': 'Cost retalive to installed capacity',
                    'Cost_per_unit': 'Cost per unit installed',
                    'Cost_multiplier': 'Cost multiplier for Switzerland', 
                    'Life': 'Lifetime'}
    for p in Parameters:
        pd.to_numeric(df[p])
    
    # Unit conversion from CHF to kCHF
    df['Cost_per_size'] /= 1000
    df['Cost_per_unit'] /= 1000
    
    # Save a copy in P and the corresponding metdata in P_meta
    for p in Parameters:
        if p != 'Life':
            for u in Units:
                physical_units = ('Years' if p == 'Life' 
                                  else 'kCHF/{}'.format(df['Size_units']))
                meta = [physical_units, Descriptions[p], df['Source'][u]]
                make_param('Eco', p, df[p][u], meta, u)
    
    return df



def resource_economics(file):
    """ Given a file name, return a dataframe of resource costs from the data forlder """
    df = data.default_data_to_df(file, 'economic', 0)
    
    # convert strings of valuesto numpy.int64
    Parameters = ['Import_cost', 'Export_cost']
    Descriptions = {'Import_cost': 'Cost to import a resource',
                    'Export_cost': 'Price at which a resource is sold'}
    
    for p in Parameters:
        pd.to_numeric(df[p])
    
    # unit conversion from CHF to kCHF
    df['Import_cost'] /= 1000
    df['Export_cost'] /= 1000
    df['Units'] = 'kCHF/kWh'
    
    # Save a copy in P and the corresponding metdata in P_meta
    for p in Parameters:
        for r in ['Elec', 'Gas']:
            physical_units = 'kCHF/kWh'
            meta = [physical_units, Descriptions[p], df['Source'][r]]
            make_param('Eco', p, df[p][r], meta, r)
    
    return df

path = os.path.join('inputs', 'precalc.h5')

P, P_meta, Categories = get_param('parameters.csv')
# Dictionnaries of values and metadata from the file 'Settings.csv'
S, S_meta = get_settings('settings.csv')
# Time discretization
Datetime_format = S['Date_format'] + ' ' + S['Time_format']

Periods, Nbr_of_time_steps, dt, Day_dates, Time, dt_end, Days_all, Hours = time_param(S)
   
Description = 'Length of a timestep in hours'
make_param('Time', 'dt', dt, ['hour', Description, 'calc'])
Description = 'Number of timesteps'
make_param('Time', 'Nbr_of_time_steps', Nbr_of_time_steps, ['integer', Description, 'calc'])
Description = 'List of timestep index'
make_param('Time', 'Periods', Periods, ['integer', Description, 'calc'])
Description = 'List of days as datetime objects'
make_param('Time', 'Day_dates', Day_dates, ['-', Description, 'calc'])
Description = 'hour:min:sec for each timestep in a day'
make_param('Time', 'Time', Time, ['-', Description, 'calc'])
    
Time_steps = {'Days': Days_all, 'Hours': Hours, 'Periods': Periods}
# Default upper bound for most variables
Bound = S['Var_bound']
# Dictionnary of variable metadata
V_meta = {}
V_meta['Header'] = ['Name', 'Value', 'Lower Bound', 'Upper Bound', 'Units', 'Decription', 'Type']
V_bounds = {}
# Dictionnary describing each constraint and its source if applicable
C_meta = {}

# Unit and resource costs
Costs_u = unit_economics('unit_costs.csv')
Costs_res = resource_economics('resource_costs.csv')



path = os.path.join('inputs', 'precalc.h5')
dic = results.get_hdf(path)
Build_cons['Heat'] = np.array(dic['build_Q'])
AD_cons_Heat = np.array(dic['AD_Q'])
Build_T = np.array(dic['build_T'])
AD_T = np.array(dic['AD_T'])

path = 'test.h5'
from results import get_hdf
dic = get_hdf(path)