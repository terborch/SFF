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
import pandas as pd

# Internal module methods
from data import (annual_to_daily, weather_param, get_param, get_profile, 
                  make_param, weather_data_to_df, time_delta, extreme_day)

P, P_meta = get_param('parameters.csv')
P_heat_load, _ = get_param('heat_load_param.csv')
P_calc, _ = get_param('calc_param.csv')

P = P.append(P_heat_load)
P = P.append(P_calc)

S, S_meta = get_param('settings.csv')
Bound = S['Model','Var_bound']
C_meta = {}
Elec_cons = get_profile(P['Profile', 'Elec_cons'])
Occupation = get_profile(P['Profile', 'Occupation'])

# Heated_area = P['Heated_area']
# Manure = P_calc['Manure']

# Non clustered parameters
filename = 'meteo_Liebensberg_10min.csv'
epsilon = 1e-6
Days = list(range(365))
Hours = list(range(24))
Ext_T, Irradiance, Index = weather_param(filename, epsilon, (Days, Hours), S['Time'])
C_meta = {}
# # Add coldest day in the 10 last year
# file = 'meteo_Liebensberg_10years.csv'
# Coldest_day = extreme_day(file, S['Time'])
# Ext_T = np.concatenate((Ext_T, [Coldest_day['Temperature'].values]))
# Irradiance = np.concatenate((Irradiance, [Coldest_day['Irradiance'].values]))
# Days = list(range(365 + 1))

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
    m.setParam("TimeLimit", S['Model', 'Solver_time_limit'])
    
    return m

def heat_load_model(Ext_T, Gains, U, C, T_min, T_max, part_load, 
                    Building=True):
    """ MILP thermodynamic model. The same model is used for the building and
        the AD. Constrain the temperature between a minimum and a maximum, 
        Constrain the lowest heat load to part_load. Minimize the total
        heat consumption and the maximum heat load.
        
        Note that in the C_meta dictionnary of constraints metadata, the last
        value is a number referencing the equation numbers in the project
        report titled Energetic Environment Economic Optimization of a Farm 
        Case study:Swiss Future Farm
        in 2020 by nils ter-borch.
    """
    m = initialize_model()
    
    n = 'temperature'
    T = m.addVars(Days, Hours, lb=0, ub=Bound, name=n)
    
    n = 'heat_load_max'
    Q_max = m.addVar(lb=0, ub=Bound, name=n)
    
    n = 'heat_load'
    C_meta['part_load'] = ['Building and AD minimum part load', 3]
    Q = m.addVars(Days, Hours, vtype='S', lb=part_load, ub=Bound, name=n)
    
    n = 'Temperature'
    C_meta[n] = ['Building and AD 1R1C thermal model', 1]
    m.addConstrs((C*(T[next_p(d,h)] - T[d,h]) == U[d]*(Ext_T[d,h] - T[d,h]) + 
                  Gains[d,h] + Q[d,h] for d in Days for h in Hours), n);
    
    n = 'Sizing'
    C_meta[n] = ['Building and AD maximum heat load', 1]
    m.addConstrs((Q[d,h] <= Q_max for d in Days for h in Hours), n);         
    
    n = 'Temperature_min'
    C_meta[n] = ['Building and AD minimum temperature', 2]
    m.addConstrs((T[d,h] >= T_min for d in Days for h in Hours), n);

    n = 'Temperature_max'
    C_meta[n] = ['Building and AD maximum temperature', 2]
    m.addConstrs((T[d,h] <= T_max for d in Days for h in Hours), n);

    C_meta['Objective'] = ['Building and AD heating control', 4]
    m.setObjective(Q_max*len(Days)*len(Hours) + 
                   sum(Q[d,h] for h in Hours for d in Days), GRB.MINIMIZE)
    
    if not Building:
        n = 'Temperature_init'
        m.addConstr(T[0,0] == T_min, n);
    # else:
    #     n = 'Temperature_init'
    #     m.addConstrs((T[d,0] == T_min + Ext_T[d,0] for d in Days), n);
    
    m.optimize()
    
    temperature = np.zeros(np.shape(Ext_T))
    heat_load = np.zeros(np.shape(Ext_T)) 
    for d in Days:
        for h in Hours:
            temperature[d,h] = T[d,h].x
            heat_load[d,h] = P['build', 'Heated_area']*Q[d,h].x
    
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
                      Clustered_days, Frequence, 
                      print_it=False, Building=True):
    """ Calculate the heating load profile and temperature profile of the
        buildings and AD. Based on the lowest part-load heating and temperature 
        limits as well as external weather paramerts gains and thermal properties.
    """
 
    # First resolution without upper temperature limit and part-load limit
    (temperature, heat_load
     ) = heat_load_model(Ext_T, Gains, U, C, T_min, 100, 0, 
                         Building=Building)
    
    # Fix part-load value based on previous highest heat load
    part_load = 0.2*np.max(heat_load)/P['build', 'Heated_area']
    
    if print_it:
        print('\n Initaial Max heat load: ', np.max(heat_load), '\n')
        
    if Building:
        # Modify U to allow the option for natural cooling above a certain T
        open_windows = np.where(
            np.min(temperature, axis=1) > P['build','T_open_windows'])[0]
        U = np.zeros(len(Ext_T))
        
        # Increse U of open windows periods with until T_max is respected
        realxation = 1.5
        while True:
            for i, _ in enumerate(U):
                if i not in open_windows:
                    U[i] = P['build','U_b']  
                else:
                    U[i] = P['build','U_b']*realxation
            try:
                (temperature, heat_load) = heat_load_model(Ext_T, Gains, U, C, 
                T_min, T_max, part_load, Building=Building)
                break
            except:
                realxation += 0.5
        if print_it:
            print('relaxation factor for U is: ', realxation)
     
    # Second resolution with upper temperature limit and part-load limit            
    (temperature, heat_load) = heat_load_model(Ext_T, Gains, U, C, T_min, T_max, 
    part_load, Building=Building)
    
    # Clustered days only
    temperature_cls = get_clustered_values(temperature, Clustered_days)
    heat_load_cls = get_clustered_values(heat_load, Clustered_days)
    total_heat_load_cls = np.sum(np.sum(heat_load_cls, axis=1)*Frequence)
    max_heat_load_cls = np.max(heat_load_cls)
    
    # Corrected values to match real data
    C_meta['Heat_load_correct'] = ['Building and AD heat load correction', 11]
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
    meta = ['kW/m^2', 'Heat gains from people', 5]
    Gains_ppl = annual_to_daily(P[c, 'Gains_ppl_annual'], Occupation)
    make_param(c, 'Gains_ppl', 'inputs.h5', meta)
    
    meta = ['kW/m^2', 'Heat gains from appliances', 7]
    Gains_elec = (P[c, 'Elec_heat_frac'] * Elec_cons / 
                  P['build', 'Heated_area'])
    make_param(c, 'Gains_elec', 'inputs.h5', meta)
    
    meta = ['kW/m^2', 'Heat gains from irradiation', 9]
    Gains_solar = P[c, 'Absorptance'] * Irradiance
    make_param(c, 'Gains_solar', 'inputs.h5', meta)
    
    meta = ['kW/m^2', 'Sum of all heat gains', 10]
    Gains = Gains_ppl + Gains_elec + Gains_solar
    make_param(c, 'Gains', 'inputs.h5', meta)
    
    # N.B. Equivalent to:
    # Gains = np.zeros((len(Days), len(Hours)))
    # for d in Days:
    #     Gains[d] = Gains_ppl + Gains_elec + Gains_solar[d]
    
    
    # C_meta['Gains_ppl'] = ['Building people gains', 4, 'P']
    # C_meta['Gains_elec'] = ['Building electric gains', 3, 'P']
    # C_meta['Gains_solar'] = ['Building solar gains', 3, 'P']
    # C_meta['Gains'] = ['Sum of all building heating gains', 3, 'P']
    return Gains


def ad_sizing():
    """ Calculates the maxium size of the AD and its dimentions relative
        to the avilable manure.
    """
    meta = {}
    
    c = 'AD'
    name = 'Capacity'
    meta[name] = ['kW', 'Rated Biogas production capacity', 'calc']
    P[c,name] = np.round(P['Farm','Biomass_prod']*P[c,'Eff'] , 2)
    
    name = 'Sludge_volume'
    meta[name] = ['m^3', 'Sludge volume capacity', 'calc']
    P[c,name] = np.ceil(P[c,'Residence_time']*P['AD','LSU']*
                        P['AD','Manure_per_cattle']/
                       (1 - P[c,'Biomass_water'])/1000 )
    
    name = 'Cyl_volume'
    meta[name] = ['m^3', 'Cylinder volume', 'calc']
    P[c,name] = np.ceil( P[c,'Sludge_volume']/P[c,'Cyl_fill'] )
    
    name = 'Cap_height'
    meta[name] = ['m', 'Height of the AD top cap', 'calc']
    P[c,name] = np.round( (P[c,'Sludge_volume']*P[c,'Cap_V_ratio']*(6/np.pi)/
                         (3*P[c,'Cap_h_ratio']**2 + 1))**(1/3), 2)
    
    name = 'Diameter'
    meta[name] = ['m', 'Diameter of the AD cylindrical body', 'calc']
    P[c,name] = np.round( P[c,'Cap_h_ratio']*P[c,'Cap_height']*2, 2)
    
    name = 'Ground_area'
    meta[name] = ['m^2', 'Ground floor area', 'calc']
    P[c,name] = np.round( np.pi*(P[c,'Diameter']/2)**2, 2)
    
    name = 'Cap_area'
    meta[name] = ['m^2', 'Surface area of the AD top cap', 'calc']
    P[c,name] = np.round( np.pi*(P[c,'Cap_height']**2 + (P[c,'Diameter']/2)**2), 2)
    
    name = 'Cyl_height'
    meta[name] = ['m', 'Height of the AD cylindrical body', 'calc']
    P[c,name] = np.round( P[c,'Cyl_volume']/(np.pi*(P[c,'Diameter']/2)**2), 2)

    make_param('AD', list(meta.keys()), P, meta)
    
def ad_gains(T_min):    
    """ Calculates the gains of the AD based on AD size and weather. 
        Concerning solar gains:    
        Since the cover surface is the same outside and inside (the temperature 
        is hotter inside but close) the heat absorbed by the cover is 
        considered to be emitted equally to the outside and inside.
    """
    meta = {}
    
    c, p = 'AD', 'Physical'
    n = 'U'
    meta[n] = ['kW/C', 'AD heat conductance', 'calc']
    P[c,n] = P[c,'Cap_area']*P[c,'U_cap']
    
    n = 'C'
    meta[n] = ['kWh/C', 'Heat capacity of the AD', 'calc']
    P[c,n] = (P[p,'Cp_water']*P[c,'Sludge_volume'] + 
               P['build','C_b']*P[c,'Ground_area'])

    C_meta['Gains_solar_AD'] = ['Heat gains from irradiation', 0, 'P']    
    metadata = ['kW', 'Heat gains from irradiation', 'calc']
    Gains_solar = P[c,'Cap_abs']*P[c,'Ground_area']*Irradiance/2
    make_param(c, 'Gains_solar', 'inputs.h5', metadata)
    
    C_meta['Losses_biomass'] = ['Heat losses due to cold biomass input', 0, 'P']
    metadata = ['kW', 'Heat gains from irradiation', 'calc']
    Losses_biomass = ((P['Farm', 'Biomass_prod']/(P[c,'Manure_HHV_dry']*
                    (1 - P[c,'Biomass_water'])))*(P[p,'Cp_water']/1000)*
                    (T_min - Ext_T))
    make_param(c, 'Losses_biomass', 'inputs.h5', metadata)
    
    n = 'Losses_ground'
    meta[n] = ['kW', 'Heat gains from irradiation', 'calc']
    P[c,n] = P[c,'Ground_losses']*P[c,'Ground_area']
    
    n = 'Gains_elec'
    meta[n] = ['kW', 'Heat gains from electricity consumption', 'calc']
    P[c,n] = P[c,'Capacity']*P[c,'Elec_cons']  
    

    metadata = ['kW/m^2', 'Sum of all heat gains and losses', 0]
    C_meta['Gains_AD'] = ['Sum of all AD heating gains and losses', 0, 'P']
    Gains = Gains_solar + (np.ones(np.shape(Ext_T))*
            (P[c,'Gains_elec'] - P[c,'Losses_ground'] - Losses_biomass))
    make_param(c, 'Gains', 'inputs.h5', metadata)
    
    make_param('AD', list(meta.keys()), P, meta)
    
    return Gains


###############################################################################
### Generate and stor heat load values
###############################################################################
def save_df_to_hdf5(key, profile, path):
    """ Save a single 2d array to a hdf5 file as a dataframe """
    df = pd.DataFrame(profile)
    with pd.HDFStore(path) as hdf:
        hdf.put(key, df, data_columns=True)
        
    
def generate(path, Clustered_days, Frequence, New_Pamar=None, New_Setting=None):
    """ Generates and stored temperature and heat load profiles for the
        building and the AD.
    """
    
    # If specified, new parameters and settings are defined before writings inputs
    if type(New_Pamar) != type(None):
        global P
        P = New_Pamar
    if type(New_Setting) != type(None):
        global S
        S = New_Setting
    
    # Building profiles
    c = 'build'
    part_load = P[c,'Heating_part_load']
    T_min, T_max = P[c,'T_min'], P[c,'T_max']
    U, C = [P[c,'U_b']]*len(Days), P[c,'C_b']
    Gains = building_gains()
    measured_heat_load = P['Farm','cons_Heat_annual']
    
    heat_load_modeled, temperature_cls = heat_load_precalc(
        part_load,
        measured_heat_load,
        Gains, 
        U,
        C,
        T_min,
        T_max,
        Clustered_days,
        Frequence,
        print_it = False,
        Building = True
        )
    
    # Add safety margin to the first max heat load
    Max_load = np.where(heat_load_modeled==heat_load_modeled.max())   
    Max_load_idx = (Max_load[0][0], Max_load[1][0])
    heat_load_modeled[Max_load_idx] *= P['build']['Safety_factor'] 
    
    save_df_to_hdf5('build_Q', heat_load_modeled, path)
    save_df_to_hdf5('build_T', temperature_cls, path)
    
    
    # AD profile
    c = 'AD'
    part_load = P[c,'Heating_part_load']
    T_min, T_max = P[c,'T_min'], P[c,'T_max']
    ad_sizing()
    Gains = ad_gains(T_min)
    U, C = [P[c,'U']]*len(Ext_T), P[c,'C']
    measured_heat_load = (P['Farm', 'Biomass_prod']*P[c,'Eff']*
                          8760*P[c,'Heat_cons'])
    
    heat_load_modeled, temperature_cls = heat_load_precalc(
        part_load,
        measured_heat_load,
        Gains, 
        U,
        C,
        T_min,
        T_max,
        Clustered_days,
        Frequence,
        print_it = False,
        Building = False
        )
    
    save_df_to_hdf5('AD_Q', heat_load_modeled, path)
    save_df_to_hdf5('AD_T', temperature_cls, path)

    print(f'Heat load profiles for the building and AD where saved to {path}')
    
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
