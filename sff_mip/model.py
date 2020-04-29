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

# Variables
from initialize_model import m, P, P_meta, S, V_meta, C_meta, Bound, Periods
from global_set import Units, U_res, G_res, Heat_cons, Heat_prod
from global_param import (Irradiance, Build_cons_Elec, Biomass_prod, Costs_u, Costs_res, df_cons, 
                          Heated_area, Ext_T)
# Functions
from global_param import annual_to_instant

"""
### Variable declaration
    #   unit_prod           dict of vars    What each unit produce during one time period
    #   unit_cons           dict of vars    What each unit produce during one time period
    #   unit_size           vars            The size of each unit
    #   unit_install        vars            Whether or not each unit is installed
    #   unit_capex          vars            capex of each unit
    #   unit_SOC            dict of vars    State of Charge of storgae units
    #   unit_charge         dict of vars    Whether or not a storgae units is charging
    #   unit_discharge      dict of vars    Whether or not a storgae units is discharging
    #   unit_T              dict of vars    temperature of each unit (only the AD)
    #   build_cons_Heat     vars            heat consumed by the building
    #   v                   dict of vars    mass flow rate of heating water
"""

from global_var import (unit_prod, unit_cons, unit_install, unit_size, unit_capex, unit_T, 
                        build_cons_Heat, unit_SOC, unit_charge, unit_discharge, v)



##################################################################################################
### Units model
##################################################################################################


import units


def cstr_unit_size(S):
    """ Size constraints for each units """
    Unit_size_limit = {}
    for u in Units:
        Unit_size_limit[u] = [S[u + '_min'], S[u + '_max']]
        
    n = 'unit_max_size'
    for u in Units:
        C_meta[n + f'[{u}]'] = [f'Upper limit on the installed capacity of {u} fixed in settings', 1]
    m.addConstrs((unit_size[u] <= Unit_size_limit[u][1] for u in Units), n);
    n = 'unit_min_size'
    for u in Units:
        C_meta[n + f'[{u}]'] = [f'Lower limit on the installed capacity of {u} fixed in settings', 1]
    m.addConstrs((unit_size[u] >= Unit_size_limit[u][0] for u in Units), n);


cstr_unit_size(S)

u = 'BOI'
units.boi(unit_prod[u], unit_cons[u], unit_size[u])

u = 'PV'
units.pv(unit_prod[u], unit_size[u], Irradiance)

u = 'BAT'
units.bat(unit_prod[u], unit_cons[u], unit_size[u], unit_SOC[u], unit_charge[u], unit_discharge[u])

u = 'AD'
units.ad(unit_prod[u], unit_cons[u], unit_size[u], unit_T[u], unit_install[u], Ext_T, Irradiance)

u = 'SOFC'
units.sofc(unit_prod[u], unit_cons[u], unit_size[u])

u = 'CGT'
units.cgt(unit_prod[u], unit_cons[u], unit_size[u], unit_SOC[u], unit_charge[u], unit_discharge[u])


##################################################################################################
### Farm thermodynamic model
##################################################################################################

c = 'build'
n = 'build_T'
V_meta[n] = ['°C', 'Interior temperature of the building', 'time']
build_T = m.addVars(Periods + [Periods[-1] + 1], lb=-Bound, ub=Bound, name= n)

P_meta[c]['Gains_ppl_t'] = ['kW/m^2', 'Heat gains from people', 'calc']
Gains_ppl = annual_to_instant(P[c]['Gains_ppl'], df_cons['Gains'].values) * int(len(Periods)/24)

P_meta[c]['Gains_elec_t'] = ['kW/m^2', 'Heat gains from appliances', 'calc']
Gains_elec = [P[c]['Elec_heat_frac'] * Build_cons_Elec[p] / Heated_area for p in Periods]

P_meta[c]['Gains_solar_t'] = ['kW/m^2', 'Heat gains from irradiation', 'calc']
Gains_solar = [P[c]['Building_absorptance'] * Irradiance[p] for p in Periods ]

P_meta[c]['Gains_t'] = ['kW/m^2', 'Sum of all heat gains', 'calc']
Gains = Gains_ppl + Gains_elec + Gains_solar

n = 'Building_temperature'
C_meta[n] = ['Building Temperature change relative to External Temperature, Gains and Losses', 5]
m.addConstrs((P[c]['C_b']*(build_T[p+1] - build_T[p]) == 
              P[c]['U_b']*(Ext_T[p] - build_T[p]) + Gains[p] + build_cons_Heat[p]/Heated_area
              for p in Periods), n);

n = 'Building_final_temperature'
C_meta[n] = ['Cycling constraint for the Building Temperate over the entire modelling Period', 5]
m.addConstr( build_T[Periods[-1] + 1] == build_T[0], n);

n = 'Building_temperature_min'
C_meta[n] = ['Lower limit on Building Temperature', 5]
m.addConstrs((build_T[p] >= P[c]['T_min'] for p in Periods), n);
C_meta[n] = ['Upper limit on Building Temperature', 5]
n = 'Building_temperature_max'
m.addConstrs((build_T[p] <= P[c]['T_max'] for p in Periods), n);

n = 'penalty'
V_meta[n] = ['MCHF', 'Isntant Penalty for deviating from the comfort temperature', 'time']
penalty = m.addVars(Periods, lb=0, ub=Bound, name=n)
n = 'penalty_a'
V_meta[n] = ['MCHF', 'Sum of Penalty for deviating from the comfort temperature', 'unique']
penalty_a = m.addVar(lb=0, ub=Bound, name=n)

n = 'comfort_delta_T'
V_meta[n] = ['°C', 'Temerature difference between comfort and actual building temperature', 'time']
delta_T_1 = m.addVars(Periods, lb=-Bound, ub=Bound, name=n)
n = 'Comfort_delta_T'
C_meta[n] = ['Temerature difference between comfort and actual building temperature', 5]
m.addConstrs((delta_T_1[p] == P[c]['T_amb'] - build_T[p] for p in Periods), n);

n = 'comfort_delta_T_abs'
V_meta[n] = ['°C', 'Absolute Temerature difference between comfort and actual building temperature',
             'time']
delta_T_abs = m.addVars(Periods, lb=0, ub=Bound, name=n)
n = 'Comfort_delta_T_abs'
C_meta[n] = ['Absolute Temerature difference between comfort and actual building temperature', 'time', 5]
m.addConstrs((delta_T_abs[p] == gp.abs_(delta_T_1[p]) for p in Periods), n);

n = 'comfort_T_penalty'
C_meta[n] = ['Instant penalty value relative to temperature difference and penalty factor', 5]
m.addConstrs((penalty[p] == delta_T_abs[p]*3.3013330297486014e-05 for p in Periods), n);

n = 'comfort_T_penalty_tot'
C_meta[n] = ['Sum of penalty value relative to instant penalty', 5]
m.addConstr(penalty_a == penalty.sum('*'), n);



##################################################################################################
### Heat cascade
##################################################################################################

g = 'General'
n = 'Heat_load_balance_AD'
C_meta[n] = ['Heat consumed by the AD relative to hot water supply and temperature delta', 5]
m.addConstrs((unit_cons['AD'][('Heat',p)] == P[g]['Cp_water']*(P['AD']['Th'] - P['AD']['Tc'])*
              (v['BOI'][('AD', p)] + v['SOFC'][('AD', p)]) for p in Periods), n);

n = 'Heat_load_balance_build'
C_meta[n] = ['Heat consumed by the Building relative to hot water supply and temperature delta', 5]
m.addConstrs((build_cons_Heat[p] == P[g]['Cp_water']*(P['build']['Th'] - P['build']['Tc'])*
              (v['BOI'][('build', p)] + v['SOFC'][('build', p)]) for p in Periods), n);

n = 'Heat_load_balance_heat_prod'
C_meta[n] = ['Heat produced by each unit relative to hot water supplied and temperature delta', 5]
m.addConstrs((unit_prod[u][('Heat',p)] == 
              P[g]['Cp_water']*(v[u][('build', p)]*(P['build']['Th'] - P['build']['Tc']) + 
                             v[u][('AD', p)]*(P['AD']['Th'] - P['AD']['Tc'])) 
              for u in Heat_prod for p in Periods), n);

n = 'AD_is_installed_heat'
C_meta[n] = ['Prevent the AD from consuming heat if it is not installed', 5]
m.addConstrs((unit_install[u]*Bound >= unit_cons[u][('Heat', p)] 
              for u in Heat_cons[1:] for p in Periods), n)
    
    

##################################################################################################
### Mass and energy balance
    #   Electricity energy balance
    #   Biomass energy balance
    #   Biogas energy balance
##################################################################################################


# Variables
n = 'grid_export_a'
V_meta[n] = ['MWh', 'Annual total resources sold by the farm', 'unique']
grid_export_a = m.addVars(G_res, lb=0, ub=Bound, name=n)

n = 'grid_import_a'
V_meta[n] = ['MWh', 'Annual total resources purchased by the farm', 'unique']
grid_import_a = m.addVars(G_res, lb=0, ub=Bound, name=n)

n = 'grid_export'
V_meta[n] = ['kW', 'Resources purchased by the farm', 'time']
grid_export = m.addVars(G_res, Periods, lb=0, ub=Bound, name=n)
n = 'grid_import'
V_meta[n] = ['kW', 'Resources purchased by the farm', 'time']
grid_import = m.addVars(G_res, Periods, lb=0, ub=Bound, name=n)

Unused_res = ['Biomass', 'Biogas', 'Gas']
n = 'unused'
V_meta[n] = ['kW', 'Resources unused or flared by the farm', 'time']
unused = m.addVars(Unused_res, Periods, lb=0, ub=Bound, name=n)
n = 'unused_a'
V_meta[n] = ['MWh', 'Annual total resources unused or flared by the farm', 'unique']
unused_a = m.addVars(Unused_res, lb=0, ub=Bound, name=n)

# Resource balances
r = 'Elec'
n = 'Balance_' + r
C_meta[n] = [f'Sum of all {r} sources equal to Sum of all {r} sinks', 5]
m.addConstrs((grid_import[(r,p)] + sum(unit_prod[up][(r,p)] for up in U_res['prod'][r])  == 
              grid_export[(r,p)] + sum(unit_cons[uc][(r,p)] for uc in U_res['cons'][r]) + 
              Build_cons_Elec[p] for p in Periods), n);
r = 'Biomass'
n = 'Balance_' + r
C_meta[n] = [f'Sum of all {r} sources equal to Sum of all {r} sinks', 5]
m.addConstrs((Biomass_prod[p] - unused[(r,p)] == unit_cons['AD'][('Biomass',p)]
              for p in Periods), n);
r = 'Biogas'
n = 'Balance_' + r
C_meta[n] = [f'Sum of all {r} sources equal to Sum of all {r} sinks', 5]
m.addConstrs((unit_prod['AD'][(r,p)] + unit_prod['CGT'][(r,p)] - unused[(r,p)] == 
              unit_cons['SOFC'][(r,p)] + unit_cons['BOI'][(r,p)] + unit_cons['CGT'][(r,p)] 
              for p in Periods), n);
r = 'Gas'
n = 'Balance_' + r
C_meta[n] = [f'Sum of all {r} sources equal to Sum of all {r} sinks', 5]
m.addConstrs((grid_import[(r,p)] - grid_export[(r,p)] - unused[(r,p)] == 
              unit_cons['SOFC'][(r,p)] + unit_cons['BOI'][(r,p)] for p in Periods), n);

# Total annual import / export
n = 'Electricity_grid_import'
C_meta[n] = ['Annual Elec import relative to instant Elec imports', 5]
m.addConstr(grid_import_a['Elec'] == sum(grid_import[('Elec',p)]/1000 for p in Periods), n);
n = 'Electricity_grid_export'
C_meta[n] = ['Annual Elec export relative to instant Elec exports', 5]
m.addConstr(grid_export_a['Elec'] == sum(grid_export[('Elec',p)]/1000 for p in Periods), n);
n = 'Gas_grid_import'
C_meta[n] = ['Annual Gas import relative to instant Gas imports', 5]
m.addConstr(grid_import_a['Gas'] == sum(grid_import[('Gas',p)]/1000 for p in Periods), n);
n = 'Gas_grid_export'
C_meta[n] = ['Annual Gas export relative to instant Gas exports', 5]
m.addConstr(grid_export_a['Gas'] == sum(grid_export[('Gas',p)]/1000 for p in Periods), n);
n = 'Unused_resources'
C_meta[n] = ['Annual unused resource relative to instant unused resources', 5]
m.addConstrs((unused_a[r] == sum(unused[(r,p)]/1000 for p in Periods) for r in Unused_res), n);

# CO2 emissions
n = 'emissions'
V_meta[n] = ['t-CO2', 'Annual total CO2 emissions', 'unique']
emissions = m.addVar(lb=-Bound, ub=Bound, name=n)

c = 'CO2'
n = 'Emissions'
C_meta[n] = ['Instant CO2 emissions relative to Elec and Gas imports', 5]
m.addConstr(emissions == grid_import_a['Elec']*P[c]['Elec'] + grid_import_a['Gas']*P[c]['Gas'], n);

###m.addConstr(emissions == (grid_import_a['Elec'] - grid_export_a['Elec'])*P[c]['Elec'] +
###                            (grid_import_a['Gas'] - grid_export_a['Gas'])*P[c]['Gas'], n);

##################################################################################################
### Economic performance indicators
    #   CAPEX 
    #   OPEX 
    #   TOTEX 
##################################################################################################

c = 'Eco'
# Annualization factor Tau
P_meta[c]['Tau'] = ['-', 'Annualization factor', 'calc']
P[c]['Tau'] = (P[c]['i']*(1 + P[c]['i'])**P[c]['n']) / ((1 + P[c]['i'])**P[c]['n'] - 1)

# Variable
n = 'capex'
V_meta[n] = ['MCHF', 'total CAPEX', 'unique']
capex = m.addVar(lb=-Bound, ub=Bound, name=n)

n = 'opex'
V_meta[n] = ['MCHF/year', 'total annual opex', 'unique']
opex = m.addVar(lb=0, ub=Bound, name=n)

n = 'totex'
V_meta[n] = ['MCHF/year', 'total annualized expenses', 'unique']
totex = m.addVar(lb=0, ub=Bound, name=n)

# Constraints
n = 'is_installed'
C_meta[n] = ['M constraint to link the boolean var unit_installed with the installed capacity', 5]
m.addConstrs((unit_install[u]*Bound >= unit_size[u] for u in Units), n);
n = 'capex'
C_meta[n] = ['Unit CAPEX relative to unit size and cost parameters', 5]
m.addConstrs((unit_capex[u] == Costs_u['Cost_multiplier'][u]*
              (unit_size[u]*Costs_u['Cost_per_size'][u] + unit_install[u]*Costs_u['Cost_per_unit'][u]) 
              for u in Units), n);

n = 'capex_sum'
C_meta[n] = ['Sum of the CAPEX of all units', 5]
m.addConstr(capex == sum([unit_capex[u] for u in Units])/1000, n);

n = 'opex_sum'
C_meta[n] = ['Sum of the OPEX of all resources', 5]
m.addConstr(opex == sum(grid_import_a[r]*Costs_res['Import_cost'][r] - 
                        grid_export_a[r]*Costs_res['Export_cost'][r] for r in G_res), n);

n = 'totex_sum'
C_meta[n] = ['TOTEX relative to the OPEX, the CAPEX and the annualization factor', 5]
m.addConstr(totex == opex + P[c]['Tau']*capex, n);

C_meta['Limit_emissions'] = ['Fix a limit to the emissions, for Pareto only', 5]
C_meta['Limit_totex'] = ['Fix a limit to the TOTEX, for Pareto only', 5]

"""
### capping emissions (Manual Pareto)
n = 'Emissions_cap'
#Cap = 27.7
#Cap = 26.5
#Cap = 26.22
Cap = 26.217
m.addConstr(emissions <= Cap, n);
"""



##################################################################################################
### Scenarios
##################################################################################################


def minimize_totex():
    m.setObjective(totex, GRB.MINIMIZE)
def minimize_opex():
    m.setObjective(opex + penalty, GRB.MINIMIZE)
def minimize_capex():
    m.setObjective(capex + penalty, GRB.MINIMIZE)
def minimize_emissions():
    m.setObjective(emissions, GRB.MINIMIZE)
def minimize_totex_tax_co2():
    m.setObjective(totex + penalty + emissions*P['CO2']['Tax'], GRB.MINIMIZE)
def pareto_constrained_totex(Limit_totex):
    m.addConstr(totex <= Limit_totex, 'Limit_totex')
    m.setObjective(emissions, GRB.MINIMIZE)
def pareto_constrained_emissions(Limit_emissions):
    print('-----------------{}--------------------'.format(Limit_emissions))
    m.addConstr(emissions <= Limit_emissions, 'Limit_emissions');
    m.setObjective(totex, GRB.MINIMIZE)
    
switcher = {'totex': minimize_totex,
            'opex': minimize_opex,
            'capex': minimize_capex,
            'emissions': minimize_emissions,
            'totex_tax_co2': minimize_totex_tax_co2,
            'pareto_totex': pareto_constrained_totex,
            'pareto_emissions': pareto_constrained_emissions
            }



##################################################################################################
### Set objective and resolve
##################################################################################################


def run(objective, Limit=None, relax=False):
    print_highlight('Objective: ' + objective)
    set_objective = switcher.get(objective)
    if 'pareto' in objective:
        set_objective(Limit)
    else:
        set_objective()
    m.optimize()
    
    # Relaxion in case of infeasible model
    if m.status == GRB.INFEASIBLE:
        print_highlight('Model INFEASIBLE!!!')
        
    if m.status == GRB.INFEASIBLE and relax:
        m.feasRelaxS(1, False, False, True)
        m.optimize()
        print_highlight('Model INFEASIBLE!!!')


def print_highlight(string):
    print('******************************************************************')
    print('******************* {} **************************'.format(string))
    print('******************************************************************')
##################################################################################################
### END
##################################################################################################

