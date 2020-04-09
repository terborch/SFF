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
    #   Electric consumption in list Farm_cons_t
    #   Biomass production in list Biomass_prod_t
    #   Unit costs in dataframe U_c
    #   Resource costs in dataframe Resource_c
"""

from global_param import Irradiance, Farm_cons_t, Biomass_prod_t, U_c, Resource_c, df_cons, Heated_area, Temperature
# Functions
from global_param import annual_to_instant

"""
### Variable declaration
    #   unit_prod_t - dict of vars - What each unit produce during one time period
    #   unit_cons_t - dict of vars - What each unit consume during one time period
    #   unit_size - vars - The size of each unit
    #   unit_install - vars - Whether or not each unit is installed
    #   u_CAPEX - vars - capex of each unit
"""

from global_var import unit_prod_t, unit_cons_t, unit_install, unit_size, u_CAPEX, flow_t



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

u = 'BOI'
units.boi(unit_cons_t[u], unit_size[u], flow_t)

u = 'PV'
units.pv(unit_prod_t[u], unit_size[u], Irradiance)

u = 'BAT'
units.bat(unit_prod_t[u], unit_cons_t[u], unit_size[u])

u = 'AD'
units.ad(unit_prod_t[u], unit_cons_t[u], unit_size[u], Temperature, Irradiance)

u = 'SOFC'
units.sofc(unit_prod_t[u], unit_cons_t[u], unit_size[u])


##################################################################################################
### Farm thermodynamic model
##################################################################################################


o = 'building_temperature'
V_meta[o] = ['°C', 'Interior temperature of the building']
T_build_t = m.addVars(Periods + [Periods[-1] + 1], lb=-100, ub=100, name= o)

o = 'heating_load_t'
q_t = m.addVars(Periods, lb=0, ub=Bound, name= o)

P_meta['Gains_ppl_t'] = ['kW/m^2', 'Heat gains from people', 'calc', 'Building']
Gains_ppl_t = annual_to_instant(P['Gains_ppl'], df_cons['Gains'].values) * int(len(Periods)/24)

P_meta['Gains_elec_t'] = ['kW/m^2', 'Heat gains from appliances', 'calc', 'Building']
Gains_elec_t = [P['Elec_heat_frac'] * Farm_cons_t[p] / Heated_area for p in Periods]

P_meta['Gains_solar_t'] = ['kW/m^2', 'Heat gains from irradiation', 'calc', 'Building']
Gains_solar_t = [P['Building_absorptance'] * Irradiance[p] for p in Periods ]

P_meta['Gains_t'] = ['kW/m^2', 'Sum of all heat gains', 'calc', 'Building']
Gains_t = Gains_ppl_t + Gains_elec_t + Gains_solar_t

o = 'Building_temperature'
m.addConstrs((P['C_b']*(T_build_t[p+1] - T_build_t[p]) == 
              P['U_b']*(Temperature[p] - T_build_t[p]) + Gains_t[p] + q_t[p]/Heated_area
              for p in Periods), o);

o = 'Building_final_temperature'
m.addConstr( T_build_t[Periods[-1] + 1] == T_build_t[0], o);

o = 'Building_temperature_constraint'
m.addConstrs((T_build_t[p] >= P['T_min_building'] for p in Periods), o);
m.addConstrs((T_build_t[p] <= P['T_max_building'] for p in Periods), o);

o = 'penalty_t'
penalty_t = m.addVars(Periods, lb=0, ub=Bound, name= o)
o = 'penalty'
penalty = m.addVar(lb=0, ub=Bound, name= o)

o = 'comfort_delta_T'
delta_T_1 = m.addVars(Periods, lb=-100, ub=100, name=o)
m.addConstrs((delta_T_1[p] == P['T_amb'] - T_build_t[p] for p in Periods), o);

o = 'comfort_delta_T_abs'
delta_T_abs = m.addVars(Periods, lb=0, ub=100, name= o)
m.addConstrs((delta_T_abs[p] == gp.abs_(delta_T_1[p]) for p in Periods), o);

o = 'comfort_T_penalty'
m.addConstrs((penalty_t[p] == delta_T_abs[p]*3.3013330297486014e-05 for p in Periods), o);

o = 'comfort_T_penalty_tot'
m.addConstr(penalty == penalty_t.sum('*'), o);



##################################################################################################
### Heat cascade
##################################################################################################


# Constraints
o = 'flow_balance'
m.addConstrs(( flow_t['m1', p] + flow_t['m2', p] == flow_t['m3', p] for p in Periods), o);

o = 'temperature_balance'
m.addConstrs((P['Th_boiler']*flow_t['m1', p] + P['Tc_building']*flow_t['m2', p] == 
              P['Th_building']*(flow_t['m1', p] + flow_t['m2', p])  for p in Periods), o);

o = 'heat_balance'
m.addConstrs((q_t[p] == flow_t['m3', p]*(P['Th_building'] - P['Tc_building'])*P['Cp_water'] 
              for p in Periods), o);

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

o = 'grid_gas_import_t'
gas_import_t = m.addVars(Periods, lb=0, ub=Bound, name= o)

# Resource balances
o = 'Balance_Electricity'
m.addConstrs((elec_import_t[p] + sum(unit_prod_t[up][('Elec',p)] for up in U_res['prod_Elec'])  == 
              elec_export_t[p] + sum(unit_cons_t[uc][('Elec',p)] for uc in U_res['cons_Elec']) + 
              Farm_cons_t[p] for p in Periods), o);
o = 'Balance_Biomass'
m.addConstrs((Biomass_prod_t[p] >= unit_cons_t['AD'][('Biomass',p)] for p in Periods), o);
o = 'Balance_Biogas'
m.addConstrs((unit_prod_t['AD'][('Biogas',p)] >= unit_cons_t['SOFC'][('Biogas',p)] 
              for p in Periods), o);
o = 'Balance_Gas'
m.addConstrs((unit_cons_t['BOI'][('Gas',p)] == gas_import_t[p] for p in Periods), o);

# Total annual import / export
o = 'Electricity_grid_import'
m.addConstr(elec_import == sum(elec_import_t[p]/1000 for p in Periods), o);
o = 'Electricity_grid_export'
m.addConstr(elec_export == sum(elec_export_t[p]/1000 for p in Periods), o);
o = 'Gas_grid_import'
m.addConstr(gas_import == sum(gas_import_t[p]/1000 for p in Periods), o);


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
m.addConstrs((u_CAPEX[u] == U_c['Cost_multiplier'][u]*
              (unit_size[u]*U_c['Cost_per_size'][u] + unit_install[u]*U_c['Cost_per_unit'][u]) 
              for u in Units), o);

o = 'capex_sum'
m.addConstr(capex == sum([u_CAPEX[u] for u in Units])/1000, o);

o = 'opex_sum'
m.addConstr(opex == (elec_import*Resource_c['Import_cost']['Elec'] - 
                     elec_export*Resource_c['Export_cost']['Elec'] +
                     gas_import*Resource_c['Import_cost']['Gas'])*12, o);

o = 'totex_sum'
m.addConstr(totex == opex + P['tau']*capex, o);



##################################################################################################
### Objective and resolution
##################################################################################################

def run(relax):

    m.setObjective(totex + penalty, GRB.MINIMIZE)
    
    m.optimize()
    
    # Relaxion in case of infeasible model
    if m.status == GRB.INFEASIBLE and relax:
        m.feasRelaxS(1, False, False, True)
        m.optimize()
        
        print('******************************************************************')
        print('******************* Model INFEASIBLE!!! **************************')
        print('******************************************************************')


##################################################################################################
### END
##################################################################################################

