"""
### Precalculates the heating load and temperature of the building and the AD
    # Thermodynamic parameters and constraints create a profile for a year
    # The profiles are cut according to the clusters
    # The profiles are tuned to match experimental data of heat consumption

    # The following profiles are stored into a hdf5 file:
        Key         Description
    #   Build_T     Building temperature profile for clustered days
    #   AD_T        AD temperature profile for clustered days
    #   Build_Q     Corrected Building heat load profile for clustered days
    #   AD_Q        Corrected AD heat load profile for clustered days
"""

# External modules
from matplotlib import pyplot as plt
import numpy as np
from gurobipy import GRB
import gurobipy as gp
import os
import pandas as pd

# Internal modules
from param_input import (P, P_meta, S, C_meta, Bound, Frequence)
from param_calc import (Build_cons, df_cons, Heated_area, Clustered_days)

# Internal module methods
from param_calc import annual_to_daily, weather_param
from results import get_hdf

# Non clustered parameters
filename = 'meteo_Liebensberg_10min.csv'
epsilon = 1e-6
Ext_T, Irradiance, Index = weather_param(filename, epsilon, clustering=False)
Days = list(range(len(Ext_T)))
Hours = list(range(24))

###############################################################################
### MILP thermodynamic model 
###############################################################################


def initialize_model():
    """ Return a blank Gurobi model and set solver timelimit """
    # Create a new model
    m = gp.Model("MIP_heat_load_model")
    # Remove previous model parameters and data
    m.resetParams()
    m.reset()
    # Set solver time limit
    m.setParam("TimeLimit", S['Solver_time_limit'])
    
    return m

def heat_load_model(Ext_T, Gains, U, C, T_min, T_max, Heated_area, part_load, 
                    Building=True):
    """ MILP thermodynamic model. The same model is used for the building and
        the AD. Constrain the temperature between a minimum and a maximum, 
        Constrain the lowest heat load to part_load. Minimize the total
        heat consumption and the maximum heat load."""
    m = initialize_model()
    
    n = 'temperature'
    T = m.addVars(Days, Hours, lb=0, ub=Bound, name=n)
    
    n = 'heat_load_max'
    Q_max = m.addVar(lb=0, ub=Bound, name=n)
    
    n = 'heat_load'
    Q = m.addVars(Days, Hours, vtype='S', lb=part_load, ub=Bound, name=n)
    
    n = 'Temperature'
    m.addConstrs((C*(T[next_p(d,h)] - T[d,h]) == U[d]*(Ext_T[d,h] - T[d,h]) + 
                  Gains[d,h] + Q[d,h] for d in Days for h in Hours), n);
    
    n = 'Sizing'
    m.addConstrs((Q[d,h] <= Q_max for d in Days for h in Hours), n);         
    
    n = 'Temperature_min'
    m.addConstrs((T[d,h] >= T_min for d in Days for h in Hours), n);

    n = 'Temperature_max'
    m.addConstrs((T[d,h] <= T_max for d in Days for h in Hours), n);

    m.setObjective(Q_max*len(Days)*len(Hours) + 
                   sum(Q[d,h] for h in Hours for d in Days), GRB.MINIMIZE)
    
    if not Building:
        n = 'Temperature_init'
        m.addConstr(T[0,0] == T_min, n);
    
    m.optimize()
    
    temperature = np.zeros(np.shape(Ext_T))
    heat_load = np.zeros(np.shape(Ext_T)) 
    for d in Days:
        for h in Hours:
            temperature[d,h] = T[d,h].x
            heat_load[d,h] = Heated_area*Q[d,h].x
    
    return temperature, heat_load



###############################################################################
### Heat load pre-calculation
###############################################################################


def next_p(d,h):
    """ Cycle through the hours - days index and returns the next period """
    if h == Hours[-1]:
        if d == Days[-1]:
            return (0, 0)
        else:
            return (d + 1, 0)
    else:
        return (d, h + 1)
    

def get_clustered_values(values, Clustered_days):
    """ Returns only the cluster days from a yearly array of daily values """
    a = np.zeros((len(Clustered_days), 24))
    for i,d in enumerate(Clustered_days):
        a[i] = values[int(d)]
    return a


def heat_load_precalc(part_load, measured_heat_load, Gains, U, C, T_min, T_max, 
                      Heated_area, print_it=False, Building=True):
    """ Calculate the heating load profile and temperature profile of the
        buildings and AD. Based on the lowest part-load heating and temperature 
        limits as well as external weather paramerts gains and thermal properties.
    """
 
    # First resolution without upper temperature limit and part-load limit
    (temperature, heat_load
     ) = heat_load_model(Ext_T, Gains, U, C, T_min, 100, Heated_area, 0, 
                         Building=Building)
    
    # Fix part-load value based on previous highest heat load
    part_load = 0.2*np.max(heat_load)/Heated_area
    
    if print_it:
        print('\n Initaial Max heat load: ', np.max(heat_load), '\n')
        
    if Building:
        # Modify U to allow the option for natural cooling above a certain T
        open_windows = np.where(
            np.min(temperature, axis=1) > P['build']['T_open_windows'])[0]
        U = np.zeros(len(Ext_T))
        
        # Increse U of open windows periods with until T_max is respected
        realxation = 1.5
        while True:
            for i, _ in enumerate(U):
                if i not in open_windows:
                    U[i] = P['build']['U_b']  
                else:
                    U[i] = P['build']['U_b']*realxation
            try:
                (temperature, heat_load) = heat_load_model(Ext_T, Gains, U, C, 
                T_min, T_max, Heated_area, part_load, Building=Building)
                break
            except:
                realxation += 0.5
        if print_it:
            print('relaxation factor for U is: ', realxation)
     
    # Second resolution with upper temperature limit and part-load limit            
    (temperature, heat_load) = heat_load_model(Ext_T, Gains, U, C, T_min, T_max, 
    Heated_area, part_load, Building=Building)
    
    # Clustered days only
    temperature_cls = get_clustered_values(temperature, Clustered_days)
    heat_load_cls = get_clustered_values(heat_load, Clustered_days)
    total_heat_load_cls = np.sum(np.sum(heat_load_cls, axis=1)*Frequence)
    max_heat_load_cls = np.max(heat_load_cls)
    
    # Corrected values to match real data
    correction_factor = measured_heat_load/total_heat_load_cls
    q_norm = heat_load_cls/(np.max(heat_load_cls) - np.min(heat_load_cls))
    heat_load_max_modeled = max_heat_load_cls*correction_factor
    heat_load_modeled = q_norm*heat_load_max_modeled

    if print_it:
        print('\n', 'Non clustered values -------------')
        print('Max Heat load: ', np.max(heat_load), '\n')
        print('Total heat load: ', np.sum(heat_load), '\n')
        x = range(len(Days)*len(Hours))
        plt.plot(x, temperature.flatten())
        plt.show()
        plt.plot(x, heat_load.flatten())
        plt.show()

        print('Clustered values -----------------')

        print('Max Heat load: ', max_heat_load_cls, '\n')
        print('Total heat load: ', total_heat_load_cls, '\n')
        
        x = range(len(Clustered_days)*len(Hours))
        plt.scatter(x, temperature_cls.flatten(), marker = ".")
        plt.show()
        plt.plot(x, heat_load_cls.flatten())
        plt.show()
        
        print('Model values -----------------')

        print('Max Heat load: ', heat_load_max_modeled, '\n')
        print('Total heat load: ', measured_heat_load, '\n')
        plt.plot(x, heat_load_modeled.flatten())
        plt.show()
    
    return heat_load_modeled, temperature_cls


def building_gains():
    """ Building gains based on building parameters and weather """
    c = 'build'
    P_meta[c]['Gains_ppl'] = ['kW/m^2', 'Heat gains from people', 'calc']
    C_meta['Gains_ppl'] = ['Building people gains', 4, 'P']
    Gains_ppl = annual_to_daily(P[c]['Gains_ppl'], df_cons['Gains'].values)
    
    P_meta[c]['Gains_elec'] = ['kW/m^2', 'Heat gains from appliances', 'calc']
    C_meta['Gains_elec'] = ['Building electric gains', 3, 'P']
    Gains_elec = P[c]['Elec_heat_frac'] * Build_cons['Elec'] / Heated_area
    
    P_meta[c]['Gains_solar'] = ['kW/m^2', 'Heat gains from irradiation', 'calc']
    C_meta['Gains_solar'] = ['Building solar gains', 3, 'P']
    Gains_solar = P[c]['Building_absorptance'] * Irradiance
        
    P_meta[c]['Gains'] = ['kW/m^2', 'Sum of all heat gains', 'calc']
    C_meta['Gains'] = ['Sum of all building heating gains', 3, 'P']
    Gains = Gains_ppl + Gains_elec + Gains_solar
    
    return Gains


def ad_sizing():
    """ Calculates the maxium size of the AD and its dimentions relative
        to the avilable manure.
    """
    c = 'AD'
    name = 'Capacity'
    P_meta[c][name] = ['kW', 'Rated Biogas production capacity', 'calc']
    P[c][name] = np.round( P[c]['Manure_prod']*P[c]['Eff'] , 2)
    
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
    P[c][name] = np.round( np.pi*P[c]['Diameter']**2/4, 2)
    
    name = 'Cap_area'
    P_meta[c][name] = ['m^2', 'Surface area of the AD top cap', 'calc']
    P[c][name] = np.round( np.pi*(P[c]['Cap_height']**2 + (P[c]['Diameter']/2)**2), 2)
    
    name = 'Cyl_height'
    P_meta[c][name] = ['m', 'Height of the AD cylindrical body', 'calc']
    P[c][name] = np.round( P[c]['Cyl_volume']/(np.pi*(P[c]['Diameter']/2)**2), 2)


def ad_gains(T_min):    
    """ Calculates the gains of the AD based on AD size and weather. 
        Concerning solar gains:    
        Since the cover emissivity is close to 1 (Hreiz) the surface is the 
        same outside and inside and the temperature is hotter inside but is 
        considered similar the heat absorbed by the cover is considered to be 
        emitted equally to the outside and inside.
    """
    c, g = 'AD', 'General'
    n = 'U'
    P_meta[c][n] = ['kW/°C', 'AD heat conductance', 'calc']
    P[c][n] = P[c]['Cap_area']*P[c]['U_cap']
    
    n = 'C'
    P_meta[c][n] = ['kWh/°C', 'Heat capacity of the AD', 'calc']
    P[c][n] = (P[g]['Cp_water']*P[c]['Sludge_volume'] + 
               P['build']['C_b']*P[c]['Ground_area'])
    
    P_meta[c]['Gains_solar'] = ['kW', 'Heat gains from irradiation', 'calc']
    Gains_solar = P[c]['Cap_abs']*P[c]['Ground_area']*Irradiance/2
    
    n = 'Losses_biomass'
    P_meta[c]['Heat_loss_biomass'] = ['kW', 'Heat gains from irradiation', 'calc']
    P[c][n] = (((P[c]['Manure_prod']/P[c]['Manure_HHV_dry'])/
                          (1 - P[c]['Biomass_water']))*(P[g]['Cp_water']/1000)*
                         (T_min - Ext_T))
    
    n = 'Losses_ground'
    P_meta[c]['Heat_loss_biomass'] = ['kW', 'Heat gains from irradiation', 'calc']
    P[c][n] = P[c]['Ground_losses']*P[c]['Ground_area']
    
    n = 'Gains_elec'
    P_meta[c][n] = ['kW', 'Heat gains from electricity consumption', 'calc']
    P[c][n] = P[c]['Capacity']*P[c]['Elec_cons']  
    
    Gains = Gains_solar + (np.ones(np.shape(Ext_T))*
            (P[c]['Gains_elec'] - P[c]['Losses_ground'] - P[c]['Losses_biomass']))
    
    return Gains


###############################################################################
### Generate and stor heat load values
###############################################################################
def save_df_to_hdf5(key, profile, path):
    """ Save a single 2d array to a hdf5 file as a dataframe """
    df = pd.DataFrame(profile)
    with pd.HDFStore(path) as hdf:
        hdf.put(key, df, data_columns=True)
        
    
def generate(file_name, directory):
    """ Generates and stored temperature and heat load profiles for the
        building and the AD.
    """
    path = os.path.join(directory, file_name)
    
    # Building profiles
    c = 'build'
    part_load = P[c]['Heating_part_load']
    T_min, T_max = P[c]['T_min'], P[c]['T_max']
    U, C = [P['build']['U_b']]*365, P['build']['C_b']
    Gains = building_gains()
    measured_heat_load = P[c]['cons_Heat_annual']
    
    heat_load_modeled, temperature_cls = heat_load_precalc(
        part_load,
        measured_heat_load,
        Gains, 
        U,
        C,
        T_min,
        T_max,
        Heated_area,
        print_it = True,
        Building = True
        )
    
    save_df_to_hdf5('build_Q', heat_load_modeled, path)
    save_df_to_hdf5('build_T', temperature_cls, path)
    
    
    # AD profile
    c = 'AD'
    part_load = P[c]['Heating_part_load']
    T_min, T_max = P[c]['T_min'], P[c]['T_max']
    ad_sizing()
    Gains = ad_gains(T_min)
    U, C = [P[c]['U']]*len(Ext_T), P[c]['C']
    measured_heat_load = (P[c]['Manure_prod']*P[c]['Eff']*8760)*P[c]['Heat_cons']
    
    heat_load_modeled, temperature_cls = heat_load_precalc(
        part_load,
        measured_heat_load,
        Gains, 
        U,
        C,
        T_min,
        T_max,
        1,
        print_it = True,
        Building = False
        )
    
    save_df_to_hdf5('AD_Q', heat_load_modeled, path)
    save_df_to_hdf5('AD_T', temperature_cls, path)

    print(f'All profiles where saved to {file_name} in the {directory} directory')
    
    # use get_hdf(path) to get back inputs in a dict format

###############################################################################
### End
###############################################################################


"""
### Alternative heat load calculation without using an MILP model

def calc_T(previous_T, Q, Ext_T, Gains, U, C):
    Delta_T = Ext_T - previous_T
    Change_T = (Q + U*Delta_T + Gains)/C
    return Change_T + previous_T
    
Heating = 0
Full_load = 100 / Heated_area #kW/m^2


for d in Days:
    for h in Hours:
        Q[d,h] = Heating*Full_load
        Build_T[next_p(d,h)] = calc_T(Build_T[d,h], Q[d,h], Ext_T[d,h], Gains[d,h], U, C)
        
        if Build_T[next_p(d,h)] < 16:
            Heating = 1
        if Build_T[next_p(d,h)] > 20:
            Heating = 0
"""  
