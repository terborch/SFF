"""
### Parameter declaration
    #   Weather parameters in list Irradiance
    #   Electric consumption in list Farm_cons_t
    #   Biomass production in list Biomass_prod_t
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


def electric_cons(Cons_profile, Annual_Elec_cons):
    """ Take the an anual electric consumption and a daily normalized consumption profile. 
        Calculate the corresponding peak load to match the profile with the consumption. 
        Return the scaled electricity consumption profile in kW.
    """
    Avrg_cons = Annual_Elec_cons/P['Hours_per_year']
    Avrg_profile = np.mean(Cons_profile)
    Peak_load = Avrg_cons/Avrg_profile
    
    return list(Cons_profile*Peak_load)


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
    df = data.default_data_to_df(file, 'economic')
    
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
    df = data.default_data_to_df(file, 'economic')
    
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

# Electricity consumption profile
file = 'consumption_profile_dummy.csv'
df_cons = data.default_data_to_df(file, 'internal', df_weather.index)
Farm_cons_t = electric_cons(df_cons['Electricity'].values, P['Annual_Elec_cons'])

# Unit and resource costs
U_c = U_costs('unit_costs.csv')
Resource_c = resource_costs('resource_costs.csv')

# Biomass potential
Biomass_prod_t = biomass_prod(P['Pigs'], P['Cows'])