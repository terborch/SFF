"""
### Parameter declaration
    #   Weather parameters in list Irradiance
    #   Electric consumption in list Farm_cons_t
    #   Biomass production in list Biomass_prod_t
    #   Heated surface area (TODO: differenciate building types)
    #   Unit costs in dataframe U_c
    #   Resource costs in dataframe Resource_c
"""

# External modules
import numpy as np
import pandas as pd
# Internal modules
from initialize_model import P, P_meta, S
from global_set import Periods
import data


def annual_to_instant(Annual, Profile_norm):
    """ Take an annual total and a corresponding daily profile normalized from 1 to 0. Calculate 
        the average instant, then the average of the normalized profile, then the corresponding
        peak value. It returns the product of the peak and normalized profile, i.e. the
        actual profile or instanteneous load.
    """
    Average = Annual / P['Hours_per_year']
    Average_profile_norm = np.mean(Profile_norm)
    Peak = Average / Average_profile_norm

    return list(Peak * Profile_norm)


def biomass_prod(Pigs, Cows):
    """ Given an number of cows and pigs, calculate the biomass potential in kW"""
    category = 'Biomass'
    P_meta['LSU'] = ['LSU', 'Number of LSU', category]
    P['LSU'] = P['Pigs']*P['LSU_pigs'] + P['Cows']
    
    P_meta['Biomass_prod'] = ['kW', 'Biomass Production', 'calc', category]
    P['Biomass_prod'] = P['LSU']*P['Manure_per_cattle']*P['Manure_HHV_dry']/24
    
    return [P['Biomass_prod'] for p in Periods]


def U_costs(file):
    """ Given a file name, return a dataframe of unit costs from the data forlder """
    df = data.default_data_to_df(file, 'economic', 0)
    
    # convert strings of valuesto numpy.int64
    pd.to_numeric(df['Cost_per_size'])
    pd.to_numeric(df['Cost_per_unit'])
    pd.to_numeric(df['Cost_multiplier'])
    pd.to_numeric(df['Life'])
    
    # unit conversion from CHF to kCHF
    df['Cost_per_size'] /= 1000
    df['Cost_per_unit'] /= 1000

    return df


def resource_costs(file):
    """ Given a file name, return a dataframe of resource costs from the data forlder """
    df = data.default_data_to_df(file, 'economic', 0)
    
    # convert strings of valuesto numpy.int64
    pd.to_numeric(df['Import_cost'])
    pd.to_numeric(df['Export_cost'])
    
    # unit conversion from CHF to kCHF
    df['Import_cost'] /= 1000
    df['Export_cost'] /= 1000
    df['Units'] = 'kCHF/kWh'
    
    return df


# Weather parameters for a summer day at Liebensberg
day = S['Date']
period_start = day
period_end = day + ' 23:50:00'
timestep = S['Timestep']
file = 'meteo_Liebensberg_10min.csv'
df_weather = data.weather_data_to_df(file, period_start, period_end, timestep)
Irradiance = list(df_weather['Irradiance'].values) # in [kW/m^2]
Temperature = list(df_weather['Temperature'].values) # in [°C]

# Electricity consumption profile
file = 'consumption_profile_dummy.csv'
df_cons = data.default_data_to_df(file, 'internal', df_weather.index)
Farm_cons_t = annual_to_instant(P['Annual_Elec_cons'], df_cons['Electricity'].values)

# Building heated surface area
file = 'buildings.csv'
df_buildings = data.default_data_to_df(file, 'inputs', 0)
Heated_area = 0
for i in df_buildings.index:
    Heated_area += (df_buildings['Ground_surface'][i] * df_buildings['Floors'][i])

# Unit and resource costs
U_c = U_costs('unit_costs.csv')
Resource_c = resource_costs('resource_costs.csv')

# Biomass potential
Biomass_prod_t = biomass_prod(P['Pigs'], P['Cows'])