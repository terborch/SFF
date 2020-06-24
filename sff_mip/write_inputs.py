"""
### Read or calculate all parameters then write them to the inputs files
    # Write the dictionnary P for signle value parameters to calc_param.csv 
    # Write each parameter array to inputs.h5 with its name as key

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
import heat_loads_calc

# Dictionnaries of values and metadata from the file 'parameters.csv'
# example: P['AD']['eff'] = 0.3 and P_meta['AD']['eff'] = ['-', 'AD efficiency', 'energyscope']
P, P_meta = data.get_param('parameters.csv')
# Dictionnaries of values and metadata from the file 'Settings.csv'
S, S_meta = data.get_param('settings.csv')
# Dictionnary describing each constraint and its source if applicable
C_meta = {}
# Dictionnary of parameters to be stored in hdf5 format
P_write = {}    
# Dictionnary of parameters to be stored in csv format
P_calc = {}


###############################################################################
### Function used in both write and read
###############################################################################       


# def param_calc(category, name, data):
#     """ Passes the value and metadata of a given parameter into P and P_meta, 
#         given a Category and a name.
#     """
#     try:
#         P_calc[category]
#     except KeyError:
#         P_calc[category] = {}
        
#     try:
#         P_calc[category][name]
#     except KeyError:
#         P_calc[category][name] = {}
    
#     P_calc[category][name] = data
  

###############################################################################
### Generate typical periods
###############################################################################


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



###############################################################################
### Generate profiles and input parameters
###############################################################################


def biomass_prod(Pigs, Cows):
    """ Given an number of cows and pigs, calculate the biomass potential in kW"""
    
    f = 'Farm'
    p = 'Physical'
    meta = ['LSU', 'Number of LSU', 'calc']
    LSU = Pigs*P[p]['LSU_pigs'] + Cows
    data.make_param(f, 'LSU', LSU, meta)
    
    meta = ['kW', 'Biomass portential', 'calc']
    C_meta['Biomass_prod'] = ['Production of manue relative to the number of LSU', 1, 'P']
    Biomass_prod = LSU*P[p]['Manure_per_cattle']*P[p]['Manure_HHV_dry']/24
    
    data.make_param(f, 'Biomass_prod', Biomass_prod, meta)


def tractor_fueling(Days, Hours, Frequence, Ext_T):
    """ Generate a fueling profile based on annual diesel consumption, 
        weather and fueling time. The fueling takes place from 18:00 to
        04:00. Check that the sum of the fueling profile equals annual 
        consumption and cause an error if not.
    """
    Daily_avg_T = np.mean(Ext_T, axis=1)
    Fueling_days = np.sum(Frequence[Daily_avg_T > P['Farm', 'Temp_tractors']])
    
    meta = ['kW/year', 'Fuel consumed by tractors in a year', 'calc' ]
    Fuel_cons = P['Farm', 'cons_Diesel_annual']*P['Physical', 'Diesel_LHV']
    data.make_param('Farm', 'Fuel_cons', Fuel_cons, meta)
    
    meta = ['kW', 'Fuel consumed by tractors during fueling', 'calc' ]
    Fueling_load = Fuel_cons/(Fueling_days*P['GFS', 'Fueling_Time'])
    data.make_param('Farm', 'Fueling_load', Fueling_load, meta)
    
    Fueling_day = np.zeros(len(Hours))
    Fueling_day[18:] = Fueling_load
    Fueling_day[:P['GFS', 'Fueling_Time']-6] = Fueling_load
    Fueling_profile = [Fueling_day if Daily_avg_T[d] > P['Farm', 'Temp_tractors']
                       else np.zeros(len(Hours)) for d in Days]
    
    if np.round(np.sum(Fueling_profile*Frequence[:, None])) == Fuel_cons:
        return Fueling_profile
    else:
        print('Error: The fueling profile does not match annual fuel consumption')
        
    
###############################################################################
### Write inputs
###############################################################################
    

def save_to_hdf(key, item, path):
    df = pd.DataFrame(item)
    with pd.HDFStore(path) as hdf:
        hdf.put(key, df)
    print(f'Item {key} saved to {path}')
    
    
def write_arrays(path, Cluster=True):
    
    if path == 'default':
        path = os.path.join('inputs', 'inputs.h5')
    
    # Time related parameters
    (Periods, Nbr_of_time_steps, dt, Day_dates, Time, dt_end, Days_all, Hours
     ) = data.time_param(S['Time'])
    
    (Days, Frequence, Time_period_map, Clustered_days
     ) = typical_days(Periods, Hours, Cluster=Cluster) 
    
    P_write['Frequence'] = Frequence
    P_write['Time_period_map'] = Time_period_map
    P_write['Days'] = Days
    
    # Hoourly weather parameters for a year at Liebensberg
    filename = 'meteo_Liebensberg_10min.csv'
    epsilon = 1e-6
    Ext_T, Irradiance, Index = data.weather_param(filename, epsilon, 
                                                  (Days_all, Hours), S['Time'], 
                                                  Clustered_days)

    # List of dates modelled
    Dates, Dates_pd = [], Index
    for d in Dates_pd: 
        Dates.append(datetime(d.year, d.month, d.day, d.hour, d.minute))
    
    # Daily building electricity consumption profile
    Build_cons = {}
    file = P['Profile']['Elec_cons']
    Elec_cons = data.get_profile(file)
    Build_cons['Elec'] = data.annual_to_daily(P['Farm']['cons_Elec_annual'], 
                                              Elec_cons)
    
    # Biomass potential
    biomass_prod(P['Farm']['Pigs'], P['Farm']['Cows'])
    
    P_write['Ext_T'] = Ext_T
    P_write['Irradiance'] = Irradiance
    P_write['Build_cons_Elec'] = Build_cons['Elec']
    
    # Load profile for tractor fueling
    P_write['Fueling_profile'] = tractor_fueling(Days, Hours, Frequence, Ext_T)


    for k in P_write.keys():
        save_to_hdf(k, P_write[k], path)  

    heat_loads_calc.generate(path, Clustered_days, Frequence)
    

###############################################################################
### END
###############################################################################



# def AD_dimentions(P, P_meta):
#     """ Given a number of LSU and a Hydrolic Residence Time (HTR) defined in the parameter.csv 
#         file estimate the AD cylindrical body volume and add it as a parameter.
#         Then given dimention ratios, the cap surface area is calculated. Similarly the cap height,
#         body height and body diameter are calculated and stored.
#     """
#     c = 'AD'
#     name = 'Sludge_volume'
#     P_meta[c][name] = ['m^3', 'Sludge volume capacity', 'calc']
#     P[c][name] = np.ceil( P[c]['Residence_time']*P[c]['LSU']*P[c]['Manure_per_cattle']/
#                        (1 - P[c]['Biomass_water'])/1000 )
    
#     name = 'Cyl_volume'
#     P_meta[c][name] = ['m^3', 'Cylinder volume', 'calc']
#     P[c][name] = np.ceil( P[c]['Sludge_volume']/P[c]['Cyl_fill'] )

#     name = 'Cap_height'
#     P_meta[c][name] = ['m', 'Height of the AD top cap', 'calc']
#     P[c][name] = np.round( (P[c]['Sludge_volume']*P[c]['Cap_V_ratio']*(6/np.pi)/
#                          (3*P[c]['Cap_h_ratio']**2 + 1))**(1/3), 2)
    
#     name = 'Diameter'
#     P_meta[c][name] = ['m', 'Diameter of the AD cylindrical body', 'calc']
#     P[c][name] = np.round( P[c]['Cap_h_ratio']*P[c]['Cap_height']*2, 2)
    
#     name = 'Ground_area'
#     P_meta[c][name] = ['m^2', 'Ground floor area', 'calc']
#     P[c][name] = np.round( np.pi*P[c]['Diameter']**2, 2)
    
#     name = 'Cap_area'
#     P_meta[c][name] = ['m^2', 'Surface area of the AD top cap', 'calc']
#     P[c][name] = np.round( np.pi*(P[c]['Cap_height']**2 + (P[c]['Diameter']/2)**2), 2)
    
#     name = 'Cyl_height'
#     P_meta[c][name] = ['m', 'Height of the AD cylindrical body', 'calc']
#     P[c][name] = np.round( P[c]['Cyl_volume']/(np.pi*(P[c]['Diameter']/2)**2), 2)


# def param_calc(category, name, value, meta, *subcategory):
#     """ Passes the value and metadata of a given parameter into P and P_meta, 
#         given a Category and a name.
#     """   
#     if not subcategory:
#         P[category][name] = value
#         P_meta[category][name] = meta
#     else:
#         subcategory  = subcategory[0]
#         try:
#             P[category][subcategory][name] = value
#         except KeyError:
#             P[category][subcategory], P_meta[category][subcategory] = {}, {}
#             P[category][subcategory][name] = value
        
#         P_meta[category][subcategory][name] = meta 


# # Building heated surface area and ground floor area
# file = 'buildings.csv'
# df_buildings = data.default_data_to_df(file, 'inputs', 0)
# Heated_area, Ground_area = 0, 0
# for i in df_buildings.index:
#     Heated_area += (df_buildings['Ground_surface'][i] * df_buildings['Floors'][i])
#     Ground_area += df_buildings['Ground_surface'][i]
# meta = ['m^2', 'Building heated surface area', 'Building']
# param_calc('Farm', 'Heated_area', [Heated_area] + meta)
# meta = ['m^2', 'Building ground surface area', 'Building']
# param_calc('Farm', 'Ground_area', [Ground_area] + meta)