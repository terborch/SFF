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
### Generate typical periods
###############################################################################


def typical_days(Periods, Hours, Cluster=True, Number_of_clusters=20):
    """ Get the clustering parameters from a pre-rendered cluster stored 
        in the clusters.h5 file. Currently accepts 10, 20, 30, 50, 100 as 
        cluster numbers. 
    """
    D = 365
    path = os.path.join('inputs', 'clusters.h5')
    Clusters = data.get_hdf(path, Series=True)
    n = f'Cluster_{Number_of_clusters}'
    Clusters[n] = list(Clusters[n].astype(int))
    Labels, Closest = Clusters[n][:D], Clusters[n][D:]
    Clusters_order = data.arrange_clusters(Labels)
    Clustered_days = data.reorder(Closest, Clusters_order)
    Frequence = data.get_frequence(Labels)
    Frequence = data.reorder(Frequence, Clusters_order)
    
    if not Cluster:
        Labels = list(range(D))
        Closest = list(range(D))
        Clustered_days = list(range(D))
        Days = list(range(D))
        Frequence = np.ones(D)

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

    # # Add extreme day
    # Frequence = np.append(Frequence, 1)
    # Clustered_days = np.append(Clustered_days, -1)



###############################################################################
### Generate profiles and input parameters
###############################################################################


def biomass_prod(file):
    """ Given an number of cows and pigs, calculate the biomass potential in kW"""
    
    A, A_meta = data.get_param(file)
    
    # Set of all animals 
    animals = set(A.index.get_level_values(0))
    
    meta = ['kW', 'Methane yield from animals', 'calc']
    C_meta['Biogas_prod'] = ['Methane yield relative to animals', 1, 'P']
    Biogas_prod = sum((A[a,'Nbr_at_farm']/A[a,'LSU'])*A[a,'Methane_yield']
                      for a in animals)/P['Physical','Hours_per_year']
    data.make_param('Farm', 'Biogas_prod', Biogas_prod, meta)
    
    meta = ['kW', 'Biomass yield from animals', 'calc']
    C_meta['Biomass_prod'] = ['Biomass relative to methane yield and AD eff', 1, 'P']
    Biomass_prod = Biogas_prod/P['AD','Eff']
    data.make_param('Farm', 'Biomass_prod', Biomass_prod, meta)


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
    
    
def write_arrays(path, Cluster=True):
    """ Precalculate and write single input parameters to calc_param.csv and 
        profile or time-dependent input parameters to inputs.h5 """
    
    # Time related parameters
    (Periods, Nbr_of_time_steps, dt, Day_dates, Time, dt_end, Days_all, Hours
     ) = data.time_param(S['Time'])
    
    (Days, Frequence, Time_period_map, Clustered_days
     ) = typical_days(Periods, Hours, Cluster=Cluster, 
                      Number_of_clusters=S['Model', 'Clusters']) 
    
    P_write['Frequence'] = Frequence
    P_write['Time_period_map'] = Time_period_map
    P_write['Days'] = Days
        
    # Hourly weather parameters for a year at Liebensberg
    filename = 'meteo_Liebensberg_10min.csv'
    epsilon = 1e-6
    Ext_T, Irradiance, Index = data.weather_param(filename, epsilon, 
                                                  (Days_all, Hours), S['Time'])
    
    # Hourly electricity emissions profile for the swiss grid
    file = 'swiss_grid_elec_emissions_2015.csv'
    df = data.open_csv(file, 'profiles', ',')
    df.drop(columns=['info'], inplace=True)
    data.to_date_time(df, 'Date', dt_format='%m/%d/%y %I:%M %p')
    Elec_CO2 = data.reshape_day_hour((df.values), *(range(365),range(24)))
    
    # Cluster weather parameters
    if Cluster:
        Ext_T = data.cluster(Ext_T, Clustered_days, Hours)
        Irradiance = data.cluster(Irradiance, Clustered_days, Hours)
        Elec_CO2 = data.cluster(Elec_CO2, Clustered_days, Hours)
    
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
    biomass_prod('animals.csv')
    
    P_write['Ext_T'] = Ext_T
    P_write['Irradiance'] = Irradiance
    P_write['Build_cons_Elec'] = Build_cons['Elec']
    P_write['Elec_CO2'] = Elec_CO2
    
    # Load profile for tractor fueling
    P_write['Fueling_profile'] = tractor_fueling(Days, Hours, Frequence, Ext_T)
    
    if path == 'default':
        path = os.path.join('inputs', 'inputs.h5')

    for k in P_write.keys():
        data.save_to_hdf(k, P_write[k], path)  

    heat_loads_calc.generate(path, Clustered_days, Frequence)
    
    
    # # Append extreme period
    # file = 'meteo_Liebensberg_10years.csv'
    # Coldest_day = data.extreme_day(file, S['Time'])
    # Ext_T = np.concatenate((Ext_T, [Coldest_day['Temperature'].values]))
    # Irradiance = np.concatenate((Irradiance, [Coldest_day['Irradiance'].values]))
    
    
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