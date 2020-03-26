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
# Internal modules


"""
### Model setup and initialization
    #   get parameter values from 'parameters.csv' into dictionnary P
    #   get settings values from 'settings.csv' into dictionnary S
    #   get the parameter Bound, the upper limit of most var from 'settings.csv'
    #   initialize the Gurobi MILP model called m
"""

from initialize_model import m, P, P_meta, S, V_meta, Bound


"""
### Declare global sets of units, resources and time periods
    #   Set of all units in the list Units
    #   Set of all resources in the list Resources
    #   Set of resource each unit produce and consume in dict Units_prod and Units_cons
    #   Set of units involved with each resource in dict U_res
    #   Set of time periods (index o to P) in list Periods
"""

from global_set import Units, Units_prod, Units_cons, U_res, Periods


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

from global_var import unit_prod_t, unit_cons_t, unit_install, unit_size, u_CAPEX



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
units.pv(unit_prod_t[u], unit_size[u], Irradiance)

u = 'BAT'
units.bat(unit_prod_t[u], unit_cons_t[u], unit_size[u], Bound)

u = 'AD'
units.ad(unit_prod_t[u], unit_cons_t[u], unit_size[u])

u = 'SOFC'
units.sofc(unit_prod_t[u], unit_cons_t[u], unit_size[u])


##################################################################################################
### Farm thermodynamic model
##################################################################################################

o = 'building_temperature'
V_meta[o] = ['°C', 'Interior temperature of the building']
T_build_t = m.addVars(Periods + [Periods[-1] + 1] + [Periods[-1] + 2], lb=-1000, ub=1000, name= o)

P_meta['Gains_ppl_t'] = ['kW/m^2', 'Heat gains from people', 'calc', 'Building']
Gains_ppl_t = annual_to_instant(P['Gains_ppl'], df_cons['Gains'].values)

P_meta['Gains_elec_t'] = ['kW/m^2', 'Heat gains from appliances', 'calc', 'Building']
Gains_elec_t = [P['Elec_heat_frac'] * Farm_cons_t[p] for p in Periods]

P_meta['Gains_solar_t'] = ['kW/m^2', 'Heat gains from irradiation', 'calc', 'Building']
Gains_solar_t = [P['Building_absorptance'] * Irradiance[p] for p in Periods ]

P_meta['Gains_t'] = ['kW/m^2', 'Sum of all heat gains', 'calc', 'Building']
Gains_t = Gains_ppl_t + Gains_elec_t + Gains_solar_t

o = 'Building_temperature'
m.addConstrs((P['C_b']*(T_build_t[p+1] - T_build_t[p]) == 
              P['U_b']*(Temperature[p] - T_build_t[p]) + Gains_t[p] for p in Periods), o);

o = 'Building_final_temperature'
m.addConstr( T_build_t[Periods[-1] + 1] == 20, o);
o = 'Building_initial_temperature'
m.addConstr( T_build_t[0] == T_build_t[Periods[-1] + 2], o);

#o = 'Gains_people'
#m.addConstrs((gains_t['people', p] ==  for p in Periods), o);

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
V_meta[o] = ['kWh', 'Electricity sold by the farm']
elec_export = m.addVar(lb=0, ub=Bound, name= o)

o = 'grid_elec_import'
V_meta[o] = ['kWh', 'Electricity purchased by the farm']
elec_import = m.addVar(lb=0, ub=Bound, name= o)

o = 'grid_elec_export_t'
elec_export_t = m.addVars(Periods, lb=0, ub=Bound, name= o)
o = 'grid_elec_import_t'
elec_import_t = m.addVars(Periods, lb=0, ub=Bound, name= o)

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
P_meta['tau'] = ['-', 'Annualization factor', 'calc', 'economic']
P['tau'] = (P['i']*(1 + P['i'])**P['n']) / ((1 + P['i'])**P['n'] - 1)

# Variable
o = 'capex'
V_meta[o] = ['kCHF', 'total CAPEX']
capex = m.addVar(lb=-Bound, ub=Bound, name= o)

o = 'opex'
V_meta[o] = ['kCHF/year', 'total annual opex']
opex = m.addVar(lb=-Bound, ub=Bound, name= o)

o = 'totex'
V_meta[o] = ['kCHF/year', 'total annualized expenses']
totex = m.addVar(lb=-Bound, ub=Bound, name= o)

# Constraints
o = 'is_installed'
m.addConstrs((unit_install[u]*Bound >= unit_size[u] for u in Units), o);
o = 'capex'
m.addConstrs((u_CAPEX[u] == U_c['Cost_multiplier'][u]*
              (unit_size[u]*U_c['Cost_per_size'][u] + unit_install[u]*U_c['Cost_per_unit'][u]) 
              for u in Units), o);

o = 'capex_sum'
m.addConstr(capex == sum([u_CAPEX[u] for u in Units]), o);

o = 'opex_sum'
m.addConstr(opex == (elec_import*Resource_c['Import_cost']['Elec'] - 
                     elec_export*Resource_c['Export_cost']['Elec'])*356*P['n'], o);

o = 'totex_sum'
m.addConstr(totex == opex + P['tau']*capex, o);



##################################################################################################
### Objective and resolution
##################################################################################################

def run(relax):

    m.setObjective(totex, GRB.MINIMIZE)
    
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

