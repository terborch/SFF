""" This module contains all functions necessary to build the Mixed Interger Linear Programming
    Model (MILP) of SFF using Gurobipy and given inputs (parameter.csv, setting.csv, data folder)
"""

# Extenral modules
import gurobipy as gp
from gurobipy import GRB
import numbers
import numpy as np
import pandas as pd

# Internal Modules
import data


##################################################################################################
### Model setup and initialization
    #   get parameter values from Parameters.csv
    #   get settings values from Settings.csv
    #   create global dictionaries of calculated parameters and units of model variables 
    #   initialize the global Gurobi MILP model called m
##################################################################################################



def param_value(file):
    """ Get values only from csv files in this directy and store them into dictionaries """
    df = pd.read_csv(file, engine = 'python')

    # Change every value into float format except the values in category Time
    for i in df.index:
        if df['Category'][i] != 'Time' and  type(df['Value'][i]) != np.float64:
            df['Value'][i] = float(df['Value'][i])
    
    df.index = df['Name']
    for c in df.columns:
        if c != 'Value':
            df.drop(columns = c, inplace = True)
    dic = df.to_dict()
    return dic['Value']


def intialize_model():
    """ Return a blank Gurobi model and set solver timelimit """
    # Create a new model
    m = gp.Model("MIP_SFF_v0.25")
    # Remove previous model parameters and data
    m.resetParams()
    m.reset()
    # Set solver time limit
    m.setParam("TimeLimit", S['Solver_time_limit'])
    
    return m


# The dictionnary P contains all model parameter values from 'Parameters.csv'
P = param_value('parameters.csv')
# The dictionnary S contains all model parameter values from 'Settings.csv'
S = param_value('settings.csv')
# Default upper bound for most variables
Bound = S['Var_bound']

# Dictionnary of the units of variables: dic_vars_unit['elec_import']
dic_vars_unit = {}
# Dictionnary of all calculated parameters: 'Name': ['Value', 'Units', 'Description', 'Category']
P_calc = {}
        
m = intialize_model()



##################################################################################################
### Global sets of units, resources and time periods
##################################################################################################


# Units and resources
Units_full_name = ['Photovoltaic Panels', 'Battery', 'Solid Oxide Fuel cell', 
                   'Anaerobic Digester']
Units = ['PV', 'BAT', 'SOFC', 'AD']
Resources = ['Elec', 'Biogas', 'Biomass']

# The resources each unit produce
Units_prod = {
    'PV':   ['Elec'],
    'BAT':  ['Elec'], 
    'SOFC': ['Elec'], 
    'AD':   ['Biogas']
    }

# The resources each unit consumes
Units_cons = {
    'BAT':  ['Elec'], 
    'SOFC': ['Biogas'], 
    'AD':   ['Biomass', 'Elec']
    }

# The units producing and consuming a given resource
U_res = {
    'prod_Elec':['PV', 'BAT', 'SOFC'],
    'cons_Elec':['BAT', 'AD']
    }

# Time sets
Hours = range(0,24)     # Index h
Periods = list(Hours)   # Index p
Hours_per_year = 365*24



##################################################################################################
### Parameter declaration
    #   Weather parameters
    #   Farm parameters
    #   Electric consumption
    #   Biomass production
    #   Unit costs
    #   Resource costs
##################################################################################################


def electric_cons(Cons_profile, Annual_Elec_cons):
    """ Take the an anual electric consumption and a daily normalized consumption profile. 
        Calculate the corresponding peak load to match the profile with the consumption. 
        Return the scaled electricity consumption profile in kW.
    """
    Avrg_cons = Annual_Elec_cons/Hours_per_year
    Avrg_profile = np.mean(Cons_profile)
    Peak_load = Avrg_cons/Avrg_profile
    
    return list(Cons_profile*Peak_load)


def biomass_prod(Pigs, Cows):
    """ Given an number of cows and pigs, calculate the biomass potential in kW"""
    category = 'Biomass'
    metadata = ['LSU', 'Number of LSU', category]
    P_calc['LSU'] = [P['Pigs']*P['LSU_pigs'] + P['Cows'], metadata]
    
    metadata = ['kW', 'Biomass Production', 'calc', category]
    P_calc['Biomass_prod'] = [P_calc['LSU'][0]*P['Manure_per_cattle']*P['Manure_HHV_dry']/24, 
                              metadata]
    
    return [P_calc['Biomass_prod'][0] for p in Periods]


def U_costs(file):
    """ Given a file name, return a dataframe of unit costs from the data forlder """
    df = data.default_data_to_df(file)
    
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
    df = data.default_data_to_df(file)
    
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
Annual_Elec_cons = 787000 # kWh
file = 'consumption_profile_dummy.csv'
df_cons = data.default_data_to_df(file, df_weather.index)
Farm_cons_t = electric_cons(df_cons['Electricity'].values, Annual_Elec_cons)

# Unit and resource costs
U_c = U_costs('unit_costs.csv')
Resource_c = resource_costs('resource_costs.csv')

# Biomass potential
Biomass_prod_t = biomass_prod(P['Pigs'], P['Cows'])



##################################################################################################
### Variable declaration
##################################################################################################


# Unit production and consumption of each resource during one period
# Variable format : unit_prod_t['PV'][('Elec',0)]
# Result format : PV_prod_t[Elec,0]
# Result format details: <unit>_<pord or cons>_t[<resource>,<period>]
unit_prod_t, U_cons_t = {}, {}
for u in Units:
    if u in Units_prod:
        unit_prod_t[u] = m.addVars(Units_prod[u], Periods, lb = 0, ub = Bound, name= u + "_prod_t")
    if u in Units_cons:
        U_cons_t[u] = m.addVars(Units_cons[u], Periods, lb = 0, ub = Bound, name= u + "_cons_t")

# Size of the installed unit
unit_size = m.addVars(Units, lb = 0, ub = Bound, name="size")

# Whether or not the unit is installed
unit_install = m.addVars(Units, lb = 0, ub = Bound, vtype=GRB.BINARY, name="install")

# CAPEX of the installed unit
U_cAPEX = m.addVars(Units, lb = 0, ub = Bound, name="CAPEX")



##################################################################################################
### Units model
##################################################################################################


import units


def cstr_unit_size(S):
    """ Size constraints for each units """
    Unit_size_limit = {}
    for u in Units:
        Unit_size_limit[u] = [0, S[u + '_max']]
    
    o = 'unit_max_size'
    m.addConstrs((unit_size[u] <= Unit_size_limit[u][1] for u in Units), o);
    
    o = 'unit_min_size'
    m.addConstrs((unit_size[u] >= Unit_size_limit[u][0] for u in Units), o);


cstr_unit_size(S)

u = 'PV'
units.pv(m, P, unit_prod_t[u], unit_size[u], Periods, Irradiance)

u = 'BAT'
units.bat(m, P, unit_prod_t[u], U_cons_t[u], unit_size[u], Periods, Bound)

u = 'AD'
units.ad(m, P, unit_prod_t[u], U_cons_t[u], unit_size[u], Periods)

u = 'SOFC'
units.sofc(m, P, unit_prod_t[u], U_cons_t[u], unit_size[u], Periods)



##################################################################################################
### Farm thermodynamic model
##################################################################################################



##################################################################################################
### Heat cascade
##################################################################################################



##################################################################################################
### Mass and energy balance
    #   Electricity energy balance
    #   Biomass energy balance
    #   Biogas energy balance
##################################################################################################


# Variables
o = 'grid_elec_export'
elec_export = m.addVar(lb=0, ub=Bound, name= o)
dic_vars_unit[o] = 'kWh'
o = 'grid_elec_import'
elec_import = m.addVar(lb=0, ub=Bound, name= o)
dic_vars_unit[o] = 'kWh'
o = 'grid_elec_export_t'
elec_export_t = m.addVars(Periods, lb=0, ub=Bound, name= o)
o = 'grid_elec_import_t'
elec_import_t = m.addVars(Periods, lb=0, ub=Bound, name= o)

# Resource balances
o = 'Balance_Electricity'
m.addConstrs((elec_import_t[p] + sum(unit_prod_t[up][('Elec',p)] for up in U_res['prod_Elec'])  == 
              elec_export_t[p] + sum(U_cons_t[uc][('Elec',p)] for uc in U_res['cons_Elec']) + 
              Farm_cons_t[p] for p in Periods), o);
o = 'Balance_Biomass'
m.addConstrs((Biomass_prod_t[p] >= U_cons_t['AD'][('Biomass',p)] for p in Periods), o);
o = 'Balance_Biogas'
m.addConstrs((unit_prod_t['AD'][('Biogas',p)] >= U_cons_t['SOFC'][('Biogas',p)] 
              for p in Periods), o);

# Total annual import / export
o = 'Electricity_grid_import'
m.addConstr(elec_import == sum(elec_import_t[p] for p in Periods), o);
o = 'Electricity_grid_export'
m.addConstr(elec_export == sum(elec_export_t[p] for p in Periods), o);



##################################################################################################
### Economic performance indicators
    #   CAPEX 
    #   OPEX 
    #   TOTEX 
##################################################################################################


# Annualization factor Tau
metadata = ['-', 'Annualization factor', 'economic']
P_calc['tau'] = [(P['i']*(1 + P['i'])**P['n']) / ((1 + P['i'])**P['n'] - 1), metadata]

# Variable
o = 'capex'
capex = m.addVar(lb=-Bound, ub=Bound, name= o)
dic_vars_unit[o] = 'kCHF'
o = 'opex'
opex = m.addVar(lb=-Bound, ub=Bound, name= o)
dic_vars_unit[o] = 'kCHF/year'
o = 'totex'
totex = m.addVar(lb=-Bound, ub=Bound, name= o)
dic_vars_unit[o] = 'kCHF/year'

# Constraints
o = 'is_installed'
m.addConstrs((unit_install[u]*Bound >= unit_size[u] for u in Units), o);
o = 'capex'
m.addConstrs((U_cAPEX[u] == U_c['Cost_multiplier'][u]*
              (unit_size[u]*U_c['Cost_per_size'][u] + unit_install[u]*U_c['Cost_per_unit'][u]) 
              for u in Units), o);

o = 'capex_sum'
m.addConstr(capex == sum([U_cAPEX[u] for u in Units]), o);

o = 'opex_sum'
m.addConstr(opex == (elec_import*Resource_c['Import_cost']['Elec'] - 
                     elec_export*Resource_c['Export_cost']['Elec'])*356*P['n'], o);

o = 'totex_sum'
m.addConstr(totex == opex + P['tau']*capex, o);



##################################################################################################
### Objective and resolution
##################################################################################################


m.setObjective(totex, GRB.MINIMIZE)

m.optimize()

# Relaxion in case of infeasible model
if m.status == GRB.INFEASIBLE:
    m.feasRelaxS(1, False, False, True)
    m.optimize()
    print('Model INFEASIBLE!!!')



##################################################################################################
### Output
##################################################################################################


import results
import os.path

from datetime import datetime

# datetime object containing current date and time
now = datetime.now()
now = now.strftime("%Y-%m-%d")
 
print("now =", now)

vars_name, vars_value, vars_unit, vars_lb, vars_ub = [], [], [], [], []
    
dict_variables = {'Variable Name': vars_name, 
                  'Result': vars_value, 
                  'Unit': vars_unit, 
                  'Lower Bound': vars_lb, 
                  'Upper Bound': vars_ub}

results.time_indep(m, vars_name, vars_value, vars_unit, vars_lb, vars_ub, dic_vars_unit, U_c)

df_results = pd.DataFrame.from_dict(dict_variables)

vars_name_t = results.time_dep_var_names(m)



run_nbr = 1

cd = os.path.join('results', 'run_{}_on_{}'.format(run_nbr, now), 'result_summary.pkl')

os.makedirs(os.path.dirname(cd), exist_ok=True)

df_results.to_pickle(cd)

df = pd.read_pickle(cd)


##################################################################################################
### Input
##################################################################################################


