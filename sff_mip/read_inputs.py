import os

import numpy as np

# Internal modules
from data import (get_param, time_param, get_hdf, open_csv, to_date_time, 
                  reshape_day_hour)

Palezieux = False
Test_sensitivity_PV = False

###############################################################################
### Function used in both write and read
###############################################################################

path = os.path.join('inputs', 'precalc.h5')

P, _ = get_param('parameters.csv')
P_calc, _ = get_param('calc_param.csv')
P_eco, _ = get_param('cost_param.csv')
P = P.append(P_calc)
P = P.append(P_eco)
# Dictionnaries of values and metadata from the file 'Settings.csv'
S, _ = get_param('settings.csv')
# S, _ = get_param('settings_palezieux.csv')
# S, _ = get_param('settings_palezieux_current.csv')
# S, _ = get_param('settings_no_WBOI.csv')
# S, _ = get_param('settings_SFF_current.csv')
# Time discretization
(Periods, Nbr_of_time_steps, dt, Day_dates, Time, dt_end, Days_all, Hours
 ) = time_param(S['Time'])

    
Time_steps = {'Days': Days_all, 'Hours': Hours, 'Periods': Periods}


# Dictionnary of variable metadata
V_meta = {}
V_meta['Header'] = ['Name', 'Value', 'Lower Bound', 'Upper Bound', 'Units', 
                    'Decription', 'Type']
V_bounds = {}
# Dictionnary describing each constraint and its source if applicable
C_meta = {}

path = os.path.join('inputs', 'inputs.h5')
if Palezieux:
    path = os.path.join('inputs', 'inputs_palezieux.h5')
# path = os.path.join('inputs', 'no_clusters.h5')
dic = get_hdf(path)

Build_cons = {}
Build_cons['Elec'] = dic['Build_cons_Elec'].values
Build_cons['Heat'] = dic['build_Q'].values
Time_period_map = dic['Time_period_map'].values
Days = list(range(len(dic['Days'])))
Ext_T = dic['Ext_T'].values
AD_cons_Heat = dic['AD_Q'].values
Frequence = dic['Frequence'].values
Irradiance = dic['Irradiance'].values
Elec_CO2 = dic['Elec_CO2'].values
Fueling = dic['Fueling_profile'].values

AD_T = dic['AD_T'].values
Build_T = dic['build_T'].values

def extreme_heat_load(Palezieux=False):
    P, _ = get_param('heat_load_param.csv')
    b = 'build'
    P_new, _ = get_param('palezieux_param.csv')
    A_b = P[b, 'Heated_area'] if not Palezieux else P_new['Farm','A_heated']
    return A_b*P[b, 'U_b']*(P[b, 'T_min'] - P[b, 'T_ext_extreme']) 


### Model variable standard bound
Bound = S['Model','Var_bound']
# Tighter bounds for the objectives especially capex of each unit
Tight = S['Model','Var_bound_tight']
# # Custom bounds for electricity import and export
# Max_heat_load = 1.5*np.max(Build_cons['Heat'])
# Max_elec_import = 1.5*np.max(Build_cons['Elec'])
# Max_elec_export = 1.1*(S['ICE','max_capacity'] + S['PV','max_capacity'] + S['SOFC','max_capacity'])
# # Custom bounds for storage charge and discharge
# Bound_sto = {}
# Bound_sto['BAT'] = min([Max_elec_export, S['BAT','max_capacity']])
# Bound_sto['CGT'] = min([S['BU','max_capacity'], S['CGT','max_capacity']])
# Bound_sto['BS'] = min([S['AD','max_capacity'], S['BS','max_capacity']])

# Extreme scenario heat load
Q_extreme = extreme_heat_load()

# Corrections concerning Tractors and fueling based on inputs
P['GFS', 'Cost_per_unit'] = P['GFS', 'Total_cost']*0.3
P['GFS', 'Cost_per_size'] = P['GFS', 'Total_cost']*0.7/np.max(Fueling)
P['GFS', 'Cost_per_unit'] += P['GFS', 'Conversion_cost']*P['Farm', 'nbr_tractors']

### Parameter changes from settings.csv
# Whether or not Wood is considered a reneable resource
if S['WBOI', 'Is_renewable']:
    pass
else:
    P['Wood', 'Emissions'] = P['Gas', 'Emissions']
    
Energy_Producer = S['Farm', 'Is_energy_producer']
if Energy_Producer:
    P['Elec', 'Export_cost'] = S['Farm', 'Feed_in_tariff']
    P['BM', 'Export_cost'] = 0.265
    
if Test_sensitivity_PV:
    P['PV', 'Cost_multiplier'] = P['PV', 'Cost_multiplier']*0.5

if Palezieux:
    P_new, _ = get_param('palezieux_param.csv')
    
    f = 'Farm'
    P[f, 'Biomass_prod'] = 1e6*P_new[f, 'Biomass']/8760
    P[f, 'Biogas_prod'] = P[f, 'Biomass_prod']*P['AD', 'Eff']
    A, _ = get_param('animals.csv')
    P[f, 'Biomass_emissions'] = 1e-6*(P_new[f, 'Cows']*
        A['Dairy_cows', 'Manure']*P['Physical', 'Manure_emissions'])
    Q_extreme = extreme_heat_load(Palezieux=True)
    
    u = 'AD'
    P[u, 'Heat_cons'] = P_new[u, 'cons_heat']
    P[u, 'Elec_cons'] = P_new[u, 'cons_elec']
    P[u, 'Cost_multiplier'] = 1
    P[u, 'Cost_per_size'] = 1e3*0.9*P_new[u, 'cost_inv']/P_new[u, 'Capacity']
    P[u, 'Cost_per_unit'] = 1e3*0.1*P_new[u, 'cost_inv']
    P[u, 'Min_size'] = 100
    P[u, 'Ref_size'] = P_new[u, 'Capacity']
    P[u, 'Maintenance'] = 0.02
    
    total_heat_load_simul = sum(sum(AD_cons_Heat[d,h] for h in Hours)*Frequence[d] for d in Days)
    measured_heat_load = 1e3*P_new[u, 'cons_heat_net']
    correction_factor = measured_heat_load/total_heat_load_simul
    q_norm = AD_cons_Heat/(np.max(AD_cons_Heat) - np.min(AD_cons_Heat))
    heat_load_max_modeled = np.max(AD_cons_Heat)*correction_factor
    AD_cons_Heat = q_norm*heat_load_max_modeled
    
    u = 'ICE'
    P[u, 'Eff_elec'] = P_new[u, 'Eff_elec']
    P[u, 'Eff_thermal'] = P_new[u, 'Eff_thermal']
    P[u, 'Cost_per_size'] = 0.9*P_new[u, 'cost_inv']/P_new[u, 'Capacity']
    P[u, 'Cost_per_unit'] = 0.1*P_new[u, 'cost_inv']
    P[u, 'Maintenance'] = P_new[u, 'cost_maint_net']/P_new[u, 'cost_inv']
    P[u, 'Min_size'] = int(P_new[u, 'Capacity']/3)
    P[u, 'Ref_size'] = P_new[u, 'Capacity']
    
    u = 'PV'
    P[u, 'max_utilisation'] = 1
    P['Farm', 'Ground_area'] = P_new['Farm', 'A_ground']
    P[u, 'Cost_multiplier'] = 1
    P[u, 'Cost_per_size'] = 0.9*P_new[u, 'cost_inv']/P_new[u, 'Capacity']
    P[u, 'Cost_per_unit'] = 0.1*P_new[u, 'cost_inv']
    P[u, 'Min_size'] = 100
    P[u, 'Ref_size'] = P_new[u, 'Capacity']

    
# Validations
print('Model inputs verification - time dependent shape: ' , np.shape(Build_cons['Heat']))
print('annual buildings heat load: ', int(sum(sum(Build_cons['Heat'][d,h] for h in Hours)*Frequence[d] for d in Days)))
print('annual buildings elec load: ', int(sum(Build_cons['Elec'])*365))
print('annual AD heat load: ', int(sum(sum(AD_cons_Heat[d,h] for h in Hours)*Frequence[d] for d in Days)))
print('biogas potential: ', int(P['Farm', 'Biogas_prod']))
