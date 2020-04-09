"""
### Parameter declaration
    #   Weather parameters in lists Irradiance and Ext_T (Exterior Temperature)
    #   Electric consumption in list Build_cons_elec
    #   Biomass production in list Biomass_prod
    #   Heated surface area (TODO: differenciate building types)
    #   Unit costs in dataframe U_c
    #   Resource costs in dataframe Resource_c
"""

# External modules
import numpy as np
import pandas as pd
# Internal modules
from initialize_model import P, P_meta, P_t, S, Periods, Time, Days
import data


def param_t(name, param, meta):
    """ Given a time dependent parameter adds its maximum, minimum and average value to the P_t{}
        dictionnary. Takes the given meta data and adds it to the P_meta dictionnary
    """
    P_t[name] = [min(param), max(param), np.mean(param)]
    P_meta[name] = meta
    
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


def AD_dimentions(P, P_meta):
    """ Given a number of LSU and a Hydrolic Residence Time (HTR) defined in the parameter.csv 
        file estimate the AD cylindrical body volume and add it as a parameter.
        Then given dimention ratios, the cap surface area is calculated. Similarly the cap height,
        body height and body diameter are calculated and stored.
    """
    name = 'AD_sludge_volume'
    P_meta[name] = ['m^3', 'AD digestate volume', 'AD']
    P[name] = np.ceil( P['AD_residence_time']*P['LSU']*P['Manure_per_cattle']/
                       (1 - P['Biomass_water'])/1000 )
    
    name = 'AD_cyl_volume'
    P_meta[name] = ['m^3', 'AD cylinder volume', 'AD']
    P[name] = np.ceil( P['AD_sludge_volume']/P['AD_cyl_fill'] )

    name = 'AD_cap_height'
    P_meta[name] = ['m', 'Height of the AD top cap', 'AD']
    P[name] = np.round( (P['AD_sludge_volume']*P['AD_cap_V_ratio']*(6/np.pi)/
                         (3*P['AD_cap_h_ratio']**2 + 1))**(1/3), 2)
    
    name = 'AD_diameter'
    P_meta[name] = ['m', 'Diameter of the AD cylindrical body', 'AD']
    P[name] = np.round( P['AD_cap_h_ratio']*P['AD_cap_height']*2, 2)
    
    name = 'AD_ground_area'
    P_meta[name] = ['m^2', 'AD ground floor area', 'AD']
    P[name] = np.round( np.pi*P['AD_diameter']**2, 2)
    
    name = 'AD_cap_area'
    P_meta[name] = ['m^2', 'Surface area of the AD top cap', 'AD']
    P[name] = np.round( np.pi*(P['AD_cap_height']**2 + (P['AD_diameter']/2)**2), 2)
    
    name = 'AD_cyl_height'
    P_meta[name] = ['m', 'Height of the AD cylindrical body', 'AD']
    P[name] = np.round( P['AD_cyl_volume']/(np.pi*(P['AD_diameter']/2)**2), 2)


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
file = 'meteo_Liebensberg_10min.csv'
df_weather = data.weather_data_to_df(file, S['Period_start'], S['Period_end'], S['Time_step'])
df_weather.drop(df_weather.tail(1).index,inplace=True)
Irradiance = list(df_weather['Irradiance'].values)
param_t('Irradiance', Irradiance, ['kW/m^2', 'Global irradiance', 'weather'])
Ext_T = list(df_weather['Temperature'].values)
param_t('Ext_T', Ext_T, ['°C', 'Exterior temperature', 'weather'])

# Electricity consumption profile
file = 'consumption_profile_dummy.csv'
df_cons = data.default_data_to_df(file, 'internal', df_weather.index)
Build_cons_elec = len(Days)*annual_to_instant(P['Annual_Elec_cons'], df_cons['Electricity'].values)
param_t('Build_cons_elec', Build_cons_elec, ['kW', 'Building electricity consumption', 'Building'])

# Building heated surface area
file = 'buildings.csv'
df_buildings = data.default_data_to_df(file, 'inputs', 0)
Heated_area = 0
for i in df_buildings.index:
    Heated_area += (df_buildings['Ground_surface'][i] * df_buildings['Floors'][i])
P['Heated_area'] = Heated_area
P_meta['Heated_area'] = ['m^2', 'Building heated surface area', 'Building']

# Dimentions of the AD
AD_dimentions(P, P_meta)

# Unit and resource costs
U_c = U_costs('unit_costs.csv')
Resource_c = resource_costs('resource_costs.csv')

# Biomass potential
Biomass_prod = biomass_prod(P['Pigs'], P['Cows'])
param_t('Biomass_prod', Biomass_prod, ['kW', 'Biomass production', 'Biomass'])