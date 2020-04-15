""" This module contains all functions necessary to build the Mixed Interger Linear Programming
    Model (MILP) of SFF using Gurobipy and given inputs (parameter.csv, setting.csv, data folder)

    #   TODO: add C_meta constrain description and source
    #   TODO: storage of metadata 
    #   TODO: storage of inputs
    #   TODO: add heat cascade
    #   TODO: add farm thermal model
"""

# External modules
from gurobipy import GRB
import gurobipy as gp
# Internal modules


"""
### Model setup and initialization
    #   get parameter values from 'parameters.csv' into dictionnary P
    #   get settings values from 'settings.csv' into dictionnary S
    #   get the parameter Bound, the upper limit of most var from 'settings.csv'
    #   initialize the Gurobi MILP model called m
    #   Set of time periods (index o to P) in list Periods
"""

from initialize_model import m, P, P_meta, S, V_meta, Bound, Periods


"""
### Declare global sets of units, resources and time periods
    #   Set of all units in the list Units
    #   Set of all resources in the list Resources
    #   Set of resource each unit produce and consume in dict Units_prod and Units_cons
    #   Set of units involved with each resource in dict U_res
"""

from global_set import Units, Units_prod, Units_cons, U_res


"""
### Parameter declaration
    #   Weather parameters in list Irradiance
    #   Electric consumption in list Build_cons_elec
    #   Biomass production in list Biomass_prod
    #   Unit costs in dataframe Costs_u
    #   Resource costs in dataframe Costs_res
"""

from global_param import Irradiance, Build_cons_elec, Biomass_prod, Costs_u, Costs_res, df_cons, Heated_area, Ext_T
# Functions
from global_param import annual_to_instant

"""
### Variable declaration
    #   unit_prod - dict of vars - What each unit produce during one time period
    #   unit_cons - dict of vars - What each unit consume during one time period
    #   unit_size - vars - The size of each unit
    #   unit_install - vars - Whether or not each unit is installed
    #   unit_capex - vars - capex of each unit
"""

from global_var import unit_prod, unit_cons, unit_install, unit_size, unit_capex, unit_T, build_cons, v, Heat_cons, Heat_prod



##################################################################################################
### Units model
##################################################################################################


import units


def cstr_unit_size(S):
    """ Size constraints for each units """
    Unit_size_limit = {}
    for u in Units:
        Unit_size_limit[u] = [S[u + '_min'], S[u + '_max']]
    
    o = 'unit_max_size'
    m.addConstrs((unit_size[u] <= Unit_size_limit[u][1] for u in Units), o);
    
    o = 'unit_min_size'
    m.addConstrs((unit_size[u] >= Unit_size_limit[u][0] for u in Units), o);


cstr_unit_size(S)

u = 'BOI'
units.boi(unit_prod[u], unit_cons[u], unit_size[u])

u = 'PV'
units.pv(unit_prod[u], unit_size[u], Irradiance)

u = 'BAT'
units.bat(unit_prod[u], unit_cons[u], unit_size[u])

u = 'AD'
units.ad(unit_prod[u], unit_cons[u], unit_size[u], unit_T[u], unit_install[u], Ext_T, Irradiance)

u = 'SOFC'
units.sofc(unit_prod[u], unit_cons[u], unit_size[u])


##################################################################################################
### Farm thermodynamic model
##################################################################################################


o = 'build_T'
V_meta[o] = ['°C', 'Interior temperature of the building']
build_T = m.addVars(Periods + [Periods[-1] + 1], lb=-Bound, ub=Bound, name= o)

P_meta['Gains_ppl_t'] = ['kW/m^2', 'Heat gains from people', 'calc', 'Building']
Gains_ppl = annual_to_instant(P['Gains_ppl'], df_cons['Gains'].values) * int(len(Periods)/24)

P_meta['Gains_elec_t'] = ['kW/m^2', 'Heat gains from appliances', 'calc', 'Building']
Gains_elec = [P['Elec_heat_frac'] * Build_cons_elec[p] / Heated_area for p in Periods]

P_meta['Gains_solar_t'] = ['kW/m^2', 'Heat gains from irradiation', 'calc', 'Building']
Gains_solar = [P['Building_absorptance'] * Irradiance[p] for p in Periods ]

P_meta['Gains_t'] = ['kW/m^2', 'Sum of all heat gains', 'calc', 'Building']
Gains = Gains_ppl + Gains_elec + Gains_solar

o = 'Building_temperature'
m.addConstrs((P['C_b']*(build_T[p+1] - build_T[p]) == 
              P['U_b']*(Ext_T[p] - build_T[p]) + Gains[p] + build_cons[('Heat',p)]/Heated_area
              for p in Periods), o);

o = 'Building_final_temperature'
m.addConstr( build_T[Periods[-1] + 1] == build_T[0], o);

o = 'Building_temperature_constraint'
m.addConstrs((build_T[p] >= P['T_min_building'] for p in Periods), o);
m.addConstrs((build_T[p] <= P['T_max_building'] for p in Periods), o);

o = 'penalty_t'
penalty_t = m.addVars(Periods, lb=0, ub=Bound, name= o)
o = 'penalty'
penalty = m.addVar(lb=0, ub=Bound, name= o)

o = 'comfort_delta_T'
delta_T_1 = m.addVars(Periods, lb=-Bound, ub=Bound, name=o)
m.addConstrs((delta_T_1[p] == P['T_amb'] - build_T[p] for p in Periods), o);

o = 'comfort_delta_T_abs'
delta_T_abs = m.addVars(Periods, lb=0, ub=Bound, name= o)
m.addConstrs((delta_T_abs[p] == gp.abs_(delta_T_1[p]) for p in Periods), o);

o = 'comfort_T_penalty'
m.addConstrs((penalty_t[p] == delta_T_abs[p]*3.3013330297486014e-05 for p in Periods), o);

o = 'comfort_T_penalty_tot'
m.addConstr(penalty == penalty_t.sum('*'), o);



##################################################################################################
### Heat cascade
##################################################################################################


o = 'Heat_load_balance_AD'
m.addConstrs((unit_cons['AD'][('Heat',p)] == P['Cp_water']*(P['Th_AD'] - P['Tc_AD'])*
              (v['BOI'][('AD', p)] + v['SOFC'][('AD', p)]) for p in Periods), o);

o = 'Heat_load_balance_build'
m.addConstrs((build_cons[('Heat',p)] == P['Cp_water']*(P['Th_build'] - P['Tc_build'])*
              (v['BOI'][('build', p)] + v['SOFC'][('build', p)]) for p in Periods), o);

o = 'Heat_load_balance_heat_prod'
m.addConstrs((unit_prod[u][('Heat',p)] == 
              P['Cp_water']*(v[u][('build', p)]*(P['Th_build'] - P['Tc_build']) + 
                             v[u][('AD', p)]*(P['Th_AD'] - P['Tc_AD'])) 
              for u in Heat_prod for p in Periods), o);

o = 'is_installed_heat'
m.addConstrs((unit_install[u]*Bound >= unit_cons[u][('Heat', p)] 
              for u in Heat_cons[1:] for p in Periods), o)
    
    

##################################################################################################
### Mass and energy balance
    #   Electricity energy balance
    #   Biomass energy balance
    #   Biogas energy balance
##################################################################################################


# Variables
o = 'grid_elec_export'
V_meta[o] = ['MWh', 'Electricity sold by the farm']
elec_export = m.addVar(lb=0, ub=Bound, name= o)

o = 'grid_elec_import'
V_meta[o] = ['MWh', 'Electricity purchased by the farm']
elec_import = m.addVar(lb=0, ub=Bound, name= o)

o = 'grid_elec_export_t'
elec_export_t = m.addVars(Periods, lb=0, ub=Bound, name= o)
o = 'grid_elec_import_t'
elec_import_t = m.addVars(Periods, lb=0, ub=Bound, name= o)

o = 'grid_gas_import'
V_meta[o] = ['MWh', 'Gas bought by the farm']
gas_import = m.addVar(lb=0, ub=Bound, name= o)

o = 'grid_gas_export'
V_meta[o] = ['MWh', 'Gas bought by the farm']
gas_export = m.addVar(lb=0, ub=Bound, name= o)

o = 'grid_gas_import_t'
gas_import_t = m.addVars(Periods, lb=0, ub=Bound, name= o)

o = 'grid_gas_export_t'
gas_export_t = m.addVars(Periods, lb=0, ub=Bound, name= o)

# Resource balances
o = 'Balance_Electricity'
m.addConstrs((elec_import_t[p] + sum(unit_prod[up][('Elec',p)] for up in U_res['prod_Elec'])  == 
              elec_export_t[p] + sum(unit_cons[uc][('Elec',p)] for uc in U_res['cons_Elec']) + 
              Build_cons_elec[p] for p in Periods), o);
o = 'Balance_Biomass'
m.addConstrs((Biomass_prod[p] >= unit_cons['AD'][('Biomass',p)] for p in Periods), o);
o = 'Balance_Biogas'
m.addConstrs((unit_prod['AD'][('Biogas',p)] >= unit_cons['SOFC'][('Biogas',p)] + 1.2*gas_export_t[p] 
              for p in Periods), o);
o = 'Balance_Gas'
m.addConstrs((unit_cons['BOI'][('Gas',p)] == gas_import_t[p] for p in Periods), o);

# Total annual import / export
o = 'Electricity_grid_import'
m.addConstr(elec_import == sum(elec_import_t[p]/1000 for p in Periods), o);
o = 'Electricity_grid_export'
m.addConstr(elec_export == sum(elec_export_t[p]/1000 for p in Periods), o);
o = 'Gas_grid_import'
m.addConstr(gas_import == sum(gas_import_t[p]/1000 for p in Periods), o);
o = 'Gas_grid_export'
m.addConstr(gas_export == sum(gas_export_t[p]/1000 for p in Periods), o);

##################################################################################################
### Economic performance indicators
    #   CAPEX 
    #   OPEX 
    #   TOTEX 
##################################################################################################


# Annualization factor Tau
P_meta['tau'] = ['-', 'Annualization factor', 'calc', 'economic']
P['tau'] = (P['i']*(1 + P['i'])**P['n']) / ((1 + P['i'])**P['n'] - 1)

# Variable
o = 'capex'
V_meta[o] = ['MCHF', 'total CAPEX']
capex = m.addVar(lb=0, ub=Bound, name= o)

o = 'opex'
V_meta[o] = ['MCHF/year', 'total annual opex']
opex = m.addVar(lb=0, ub=Bound, name= o)

o = 'totex'
V_meta[o] = ['MCHF/year', 'total annualized expenses']
totex = m.addVar(lb=0, ub=Bound, name= o)

# Constraints
o = 'is_installed'
m.addConstrs((unit_install[u]*Bound >= unit_size[u] for u in Units), o);
o = 'capex'
m.addConstrs((unit_capex[u] == Costs_u['Cost_multiplier'][u]*
              (unit_size[u]*Costs_u['Cost_per_size'][u] + unit_install[u]*Costs_u['Cost_per_unit'][u]) 
              for u in Units), o);

o = 'capex_sum'
m.addConstr(capex == sum([unit_capex[u] for u in Units])/1000, o);

o = 'opex_sum'
m.addConstr(opex == (elec_import*Costs_res['Import_cost']['Elec'] - 
                     elec_export*Costs_res['Export_cost']['Elec'] +
                     gas_import*Costs_res['Import_cost']['Gas'] -
                     gas_export*Costs_res['Export_cost']['Gas']), o);

o = 'totex_sum'
m.addConstr(totex == opex + P['tau']*capex, o);



##################################################################################################
### Objective and resolution
##################################################################################################


def run(relax):
    m.setObjective(totex + penalty, GRB.MINIMIZE)
    
    m.optimize()
    
    # Relaxion in case of infeasible model
    if m.status == GRB.INFEASIBLE:
        print('******************************************************************')
        print('******************* Model INFEASIBLE!!! **************************')
        print('******************************************************************')
        
    if m.status == GRB.INFEASIBLE and relax:
        m.feasRelaxS(1, False, False, True)
        m.optimize()
        
        print('******************************************************************')
        print('******************* Model INFEASIBLE!!! **************************')
        print('******************************************************************')


##################################################################################################
### END
##################################################################################################

