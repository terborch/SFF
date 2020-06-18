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
import os
# Internal modules
from param_input import (make_param, P, P_meta, S, C_meta, Days_all, Hours, 
                         Clustered_days)
from global_set import Units
import data
import results
    
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
    Parameters = ['Cost_per_size', 'Cost_per_unit', 'Cost_multiplier', 'Life', 
                  'Maintenance', 'LCA']
    Descriptions = {'Cost_per_size': 'Cost retalive to installed capacity',
                    'Cost_per_unit': 'Cost per unit installed',
                    'Cost_multiplier': 'Cost multiplier for Switzerland', 
                    'Life': 'Lifetime',
                    'Maintenance': 'Yearly maintenance cost in percent CAPEX',
                    'LCA': 'LCA emissions from construction'}
    for p in Parameters:
        pd.to_numeric(df[p])
    
    # Unit conversion from CHF to kCHF
    df['Cost_per_size'] /= 1000
    df['Cost_per_unit'] /= 1000
    
    # Save a copy in P and the corresponding metdata in P_meta
    SI_units = {'Life': 'Years', 
                'LCA': 'tCO2/S',
                'Maintenance': '-',
                'Cost_per_size': 'CHF/S',
                'Cost_per_unit': 'CHF',
                'Cost_multiplier': '-'}
    
    for p in Parameters:
        for u in Units:
            SI_unit = (SI_units[p] if 'S' not in SI_units[p]
                       else SI_units[p].replace('S', df['Size_units'][u]))
            meta = [SI_unit, Descriptions[p], df['Source'][u]]
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


def weather_param(file, epsilon, clustering=True):
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


# Hoourly weather parameters for a year at Liebensberg
filename = 'meteo_Liebensberg_10min.csv'
epsilon = 1e-6
Ext_T, Irradiance, Index = weather_param(filename, epsilon, clustering=True)

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

# Unit and resource costs
Costs_u = unit_economics('unit_costs.csv')
Costs_res = resource_economics('resource_costs.csv')


path = os.path.join('inputs', 'precalc.h5')
dic = results.get_hdf(path)
Build_cons['Heat'] = np.array(dic['build_Q'])
AD_cons_Heat = np.array(dic['AD_Q'])
Build_T = np.array(dic['build_T'])
AD_T = np.array(dic['AD_T'])


#AD_dimentions(P, P_meta)

c = 'AD'
name = 'Capacity'
P_meta[c][name] = ['kW', 'Rated Biogas production capacity', 'calc']
P[c][name] = np.round( P[c]['Manure_prod']*P[c]['Eff'] , 2)


def make_df(df, Cat, Name, Val, Meta):
    if 'Â' in Meta[0]:
        Meta[0] = Meta[0].replace('Â', '')
    row = {'Category': Cat, 
           'Name': Name, 
           'Value': Val,
           'Units': Meta[0],
           'Description': Meta[1],
           'Source': Meta[2]}
    return df.append(row, ignore_index=True)




df = pd.DataFrame(columns=['Category', 'Name', 'Value', 'Units', 'Description', 'Source'])
i = 0
#keys = list(Units) + list(set(P.keys()) - set(Units))

for k1 in P.keys():
    for k2 in P[k1].keys():
        if np.shape(P[k1][k2]) == () and type(P[k1][k2]) != dict:
            pass
            # df = make_df(df, k1, k2, P[k1][k2], P_meta[k1][k2])
        elif type(P[k1][k2]) == dict:
            for k3 in P[k1][k2].keys():
                df = make_df(df, k2, k3,  P[k1][k2][k3], P_meta[k1][k2][k3])

df.sort_values(by=['Category', 'Name'], inplace=True, ignore_index=True)

# keys = list(set(P.keys()) - set(Units))

# for k1 in keys:
#     for k2 in P[k1].keys():
#         if np.shape(P[k1][k2]) == () and type(P[k1][k2]) != dict:
#             df = make_df(df, k1, k2, P[k1][k2], P_meta[k1][k2])


df.to_csv('test.csv')