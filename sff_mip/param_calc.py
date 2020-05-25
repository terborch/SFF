"""
### Methods
    #   annualize       takes the number of years and interest rate as parameters
                        and returns the annualization factor
### Parameter declaration
    #   Ext_T           list of external temperature values averaged for each period
    #   Irradiance      list of global Irradiance values summed over each period
    #   Dates           list of datetime objects corresponding to all dates and times modeled
    #   Build_cons_Elec list of daily electric consumptionr epeaded over each day
    #   Heated_area     the total heated floor area
    #   Biomass_prod    the amount of biomass produced for each period
    #   Costs_u         dataframe of Unit investment cost parameters and lifetime
    #   Costs_res       dataframe of Resource import and export prices
"""

# External modules
import datetime
import numpy as np
import pandas as pd
# Internal modules
from param_input import (make_param, P, P_meta, S, C_meta, Days_all, Hours, 
                         Clustered_days)
from global_set import Units
import data

    
def annual_to_daily(Annual, Profile_norm):
    """ Take an annual total and a corresponding daily profile normalized from 1 to 0. Calculate 
        the average instant, then the average of the normalized profile, then the corresponding
        peak value. It returns the product of the peak and normalized profile, i.e. the
        actual profile or instanteneous load.
    """
    Average = Annual / P['Time']['Hours_per_year']
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


def annualize(n, i):
    """ Takes the number of years and interest rate as parameters and returns 
        the annualization factor Tau
    """
    return (i*(1 + i)**n) / ((1 + i)**n - 1)


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


def reshape_day_hour(hourly_indexed_list, Days_all, Hours):
    """ Reshape a list with hourly index to a list of list with daily and hour 
    in day index """
    return (np.reshape(hourly_indexed_list, (len(Days_all), len(Hours))))


def cluster(a, Clustered_days):
    clustered_a = np.zeros((len(Clustered_days), len(Hours)))
    for i, c in enumerate(Clustered_days):
        clustered_a[i] = a[int(c)]
    return clustered_a


# Weather parameters for a summer day at Liebensberg
file = 'meteo_Liebensberg_10min.csv'
df_weather = data.weather_data_to_df(file, S['Period_start'], S['Period_end'], S['Time_step'])
df_weather.drop(df_weather.tail(1).index,inplace=True)

# External temperature - format Ext_T[Day_index,Hour_index]
epsilon = 1e-6
Ext_T = reshape_day_hour((df_weather['Temperature'].values), Days_all, Hours)
Ext_T = cluster(Ext_T, Clustered_days)
Ext_T[np.abs(Ext_T) < epsilon] = 0
P_meta['Timedep']['Ext_T'] = ['°C', 'Exterior temperature', 'agrometeo.ch']

# Global irradiance
Irradiance = reshape_day_hour((df_weather['Irradiance'].values), Days_all, Hours)
Irradiance = cluster(Irradiance, Clustered_days)
Irradiance[np.abs(Irradiance) < epsilon] = 0
P_meta['Timedep']['Irradiance'] = ['kW/m^2', 'Global irradiance', 'agrometeo.ch']

# List of dates modelled
Dates, Dates_pd = [], df_weather.index
for d in Dates_pd: 
    Dates.append(datetime.datetime(d.year, d.month, d.day, d.hour, d.minute))

# Daily building electricity consumption profile
meta = ['kW', 'Building electricity consumption', 'calc']
file = 'consumption_profile_dummy.csv'
df_cons = data.default_data_to_df(file, 'internal', df_weather.index)
Build_cons_Elec = annual_to_daily(P['build']['cons_Elec_annual'], df_cons['Electricity'].values)
make_param('Timedep', 'Build_cons_Elec', Build_cons_Elec, meta)

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

# Unit and resource costs
Costs_u = unit_economics('unit_costs.csv')
Costs_res = resource_economics('resource_costs.csv')




AD_dimentions(P, P_meta)
