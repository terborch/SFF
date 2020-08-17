""" This module contains all functions necessary to build the Mixed Interger Linear Programming
    Model (MILP) of SFF using Gurobipy and given inputs (parameter.csv, setting.csv, data folder)

    Note that in the C_meta dictionnary of constraints metadata, the last
    value is a number referencing the equation numbers in the project
    report titled Energetic Environment Economic Optimization of a Farm 
    Case study:Swiss Future Farm
    in 2020 by nils ter-borch.
"""

# External modules
from gurobipy import GRB
import gurobipy as gp
# Internal modules
from global_set import Units, U_res, G_res, U_prod
from read_inputs import (P, S, V_meta, C_meta, Bound, Tight, 
                         Periods, Days, Hours, Frequence, 
                         Irradiance, Ext_T, Build_cons, AD_cons_Heat, Fueling,
                         Elec_CO2, Energy_Producer, Q_extreme)
# Functions
from data import annualize, get_param
import variables
import units

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

def initialize_model():
    """ Return a blank Gurobi model and set solver timelimit """
    # Create a new model
    m = gp.Model("MIP_SFF_v0.54")
    # Remove previous model parameters and data
    m.resetParams()
    m.reset()
    # Set solver time limit
    m.setParam("TimeLimit", S['Model','Solver_time_limit'])
    
    return m


###############################################################################
### Units model
###############################################################################

def cstr_unit_size(m, S, unit_size):
    """ Size constraints for each units """
        
    n = 'unit_max_size'
    for u in Units:
        C_meta[n + f'[{u}]'] = [f'Upper limit on the installed capacity of {u} fixed in settings', 0]
    m.addConstrs((unit_size[u] <= S[u, 'max_capacity'] for u in Units), n);
    n = 'unit_min_size'
    for u in Units:
        C_meta[n + f'[{u}]'] = [f'Lower limit on the installed capacity of {u} fixed in settings', 0]
    m.addConstrs((unit_size[u] >= S[u, 'min_capacity'] for u in Units), n);
    n = 'unit_min_available_size'
    


def model_units(m, Days, Hours, Periods, unit_prod, unit_cons, unit_size, 
                unit_SOC, unit_charge, unit_discharge, unit_install, P):
    
    u = 'GBOI'
    units.gboi(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], P)
    
    u = 'WBOI'
    units.wboi(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], P)
    
    u = 'AHP'
    units.ahp(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], P)
    
    u = 'GHP'
    units.ghp(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], P)
    
    u='EH'
    units.eh(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], P)
    
    u = 'PV'
    units.pv(m, Days, Hours, unit_prod[u], unit_size[u], Irradiance, P)
    
    u = 'AD'
    units.ad(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], 
             AD_cons_Heat, unit_install[u], P)
    
    u = 'SOFC'
    units.sofc(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], P)
    
    u = 'ICE'
    units.ice(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], P)
    
    u = 'BAT'
    units.bat(m, Periods, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], 
              unit_SOC[u], unit_charge[u], unit_discharge[u], unit_install[u], P)
    
    u = 'CGT'
    units.cgt(m, Periods, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], 
              unit_SOC[u], unit_charge[u], unit_discharge[u], unit_install[u], P)
    
    u = 'BS'
    units.bs(m, Periods, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], 
              unit_SOC[u], unit_charge[u], unit_discharge[u], unit_install[u], P)
    
    u = 'GCSOFC'
    units.gcsofc(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], P)
    
    u = 'BU'
    units.bu(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], P)
    
    u = 'GFS'
    units.gfs(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], U_prod[u], P)
    
    u = 'GI'
    units.gi(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], P)
    


##################################################################################################
### Mass and energy balance
    #   Electricity energy balance
    #   Biomass energy balance
    #   Biogas energy balance
##################################################################################################

def model_energy_balance(m, Days, Hours, unit_cons, unit_prod, unit_install):
    # Variables
    n = 'grid_export_a'
    V_meta[n] = ['MWh', 'Annual total resources sold by the farm', 'unique']
    grid_export_a = m.addVars(G_res, lb=0, ub=Bound, name=n)
    
    n = 'grid_import_a'
    V_meta[n] = ['MWh', 'Annual total resources purchased by the farm', 'unique']
    grid_import_a = m.addVars(G_res, lb=0, ub=Bound, name=n)
    
    n = 'grid_export'
    V_meta[n] = ['kW', 'Resources purchased by the farm', 'time']
    grid_export = m.addVars(G_res, Days, Hours, lb=0, ub=Bound, name=n)
    n = 'grid_import'
    V_meta[n] = ['kW', 'Resources purchased by the farm', 'time']
    grid_import = m.addVars(G_res, Days, Hours, lb=0, ub=Bound, name=n)
    
    Unused_res = ['Biomass', 'Biogas', 'Gas', 'Wood', 'Heat', 'Diesel', 'BM']
    n = 'unused'
    V_meta[n] = ['kW', 'Resources unused or flared by the farm', 'time']
    unused = m.addVars(Unused_res, Days, Hours, lb=0, ub=Bound, name=n)
    n = 'unused_a'
    V_meta[n] = ['MWh', 'Annual total resources unused or flared by the farm', 'unique']
    unused_a = m.addVars(Unused_res, lb=0, ub=Bound, name=n)
    
    n = 'grid_import_elec'
    V_meta[n] = ['-', 'Decision var on importing elec', 'unique']
    grid_import_elec = m.addVars(Days, Hours, vtype=GRB.BINARY, name=n)
    n = 'grid_export_elec'
    V_meta[n] = ['-', 'Decision var on exporting elec', 'unique']
    grid_export_elec = m.addVars(Days, Hours, vtype=GRB.BINARY, name=n)
    
    # Resource balances
    r = 'Elec'
    n = 'Balance_' + r
    C_meta[n] = [f'Sum of all {r} sources equal to Sum of all {r} sinks', 59]
    m.addConstrs((
        grid_import[r,d,h] + sum(unit_prod[up][r,d,h] for up in U_res['prod'][r]) == 
        grid_export[r,d,h] + sum(unit_cons[uc][r,d,h] for uc in U_res['cons'][r]) + 
        Build_cons['Elec'][h] for d in Days for h in Hours), n);
    
    r = 'Biogas'
    n = 'Balance_' + r
    U_prod_biogas = [u for u in U_res['prod'][r] if u != 'GCSOFC']
    U_cons_biogas = [u for u in U_res['cons'][r] if u != 'SOFC']
    C_meta[n] = [f'Sum of all {r} sources equal to Sum of all {r} sinks', 64]
    m.addConstrs((sum(unit_prod[u][r,d,h] for u in U_prod_biogas) - unused[r,d,h] ==
                    sum(unit_cons[u][r,d,h] for u in U_cons_biogas)
                    # unit_cons['GCSOFC'][r,d,h] + unit_cons['GBOI'][r,d,h] + 
                    # unit_cons['ICE'][r,d,h] + unit_cons['CGT'][r,d,h] +
                    # unit_cons['GFS'][r,d,h] 
                  for d in Days for h in Hours), n);
    
    r = 'BM'
    n = 'Balance_' + r
    U_prod_bm = [u for u in U_res['prod'][r] if u not in ('GCSOFC', 'GI', 'GFS')]
    U_cons_bm = [u for u in U_res['cons'][r] if u not in ('SOFC',)]
    C_meta[n] = [f'Sum of all {r} sources equal to Sum of all {r} sinks', 66]
    m.addConstrs((grid_import[r,d,h] - grid_export[r,d,h] - unused[r,d,h] + 
                  sum(unit_prod[up][r,d,h] for up in U_prod_bm) == 
                  sum(unit_cons[uc][r,d,h] for uc in U_cons_bm)
                  for d in Days for h in Hours), n);
    
    n = 'Balance_Biogas_cleaned_for_SOFC'
    C_meta[n] = ['SOFC only consumed Biogas and BM that is pre-cleaned', 65]
    m.addConstrs((unit_prod['GCSOFC'][r,d,h] == unit_cons['SOFC'][r,d,h] 
                  for r in ['Biogas', 'BM'] for d in Days for h in Hours), n);
    
    n = 'Exporting_biomethane'
    C_meta[n] = ['Everything produced by GI is exported', 67]
    m.addConstrs((unit_prod['GI']['BM',d,h] == grid_export['BM',d,h] 
                  for d in Days for h in Hours), n);
    
    r = 'Biomass'
    n = 'Balance_' + r
    C_meta[n] = [f'Sum of all {r} sources equal to Sum of all {r} sinks', 70]
    m.addConstrs((P['Farm','Biomass_prod'] - unused[r,d,h] == unit_cons['AD'][r,d,h]
                  for d in Days for h in Hours), n);

    r = 'Gas'
    n = 'Balance_' + r
    C_meta[n] = [f'Sum of all {r} sources equal to Sum of all {r} sinks', 71]
    m.addConstrs((grid_import[r,d,h] - grid_export[r,d,h] - unused[r,d,h] == 
                  sum(unit_cons[uc][r,d,h] for uc in U_res['cons'][r]) 
                  for d in Days for h in Hours), n);
    
    r = 'Wood'
    n = 'Balance_' + r
    C_meta[n] = [f'Sum of all {r} sources equal to Sum of all {r} sinks', 72]
    m.addConstrs((grid_import[r,d,h] - grid_export[r,d,h] - unused[r,d,h] == 
                  unit_cons['WBOI'][r,d,h] for d in Days for h in Hours), n);
    
    r = 'Diesel'
    n = 'Balance_' + r
    C_meta[n] = [f'Sum of all {r} sources equal to Sum of all {r} sinks', 73]
    m.addConstrs((grid_import[r,d,h] - grid_export[r,d,h] - unused[r,d,h] == 
                  Fueling[d,h]*(1 - unit_install['GFS'])
                  for d in Days for h in Hours), n);
    
    r = 'Tractor_fuel'
    n = 'Balance_' + r
    C_meta[n] = [f'Sum of all {r} sources equal to Sum of all {r} sinks', 68]
    m.addConstrs((unit_prod['GFS']['BM',d,h] + unit_prod['GFS']['Gas',d,h] == 
                  Fueling[d,h]*unit_install['GFS'] 
                  for d in Days for h in Hours), n);
    
    # Heat balance
    r = 'Heat'
    n = 'Balance_' + r
    C_meta[n] = ['Heat sinks equal to heat sources', 69]
    m.addConstrs((sum(unit_prod[up][r,d,h] for up in U_res['prod'][r]) ==
                  unit_cons['AD'][r,d,h] + Build_cons[r][d,h] + unused[r,d,h]                  
                  for d in Days for h in Hours), n);
    
    # Total annual import / export
    n = f'{r}_grid_import'
    C_meta[n] = [f'Annual {r} import relative to instant {r} imports', 74]
    m.addConstrs((grid_import_a[r] == 1/1000*sum(sum(
        grid_import[r,d,h] for h in Hours)*Frequence[d] for d in Days)
        for r in G_res), n);
    
    n = f'{r}_grid_export'
    C_meta[n] = [f'Annual {r} export relative to instant {r} exports', 74]
    m.addConstrs((grid_export_a[r] == 1/1000*sum(sum(
        grid_export[r,d,h] for h in Hours)*Frequence[d] for d in Days) 
        for r in G_res), n);
    
    n = 'Unused_resources'
    C_meta[n] = ['Annual unused resource relative to instant values', 74]
    m.addConstrs((unused_a[r] == 1/1000*sum(sum(
        unused[r,d,h] for h in Hours)*Frequence[d] 
        for d in Days) for r in Unused_res), n);
    
    # Feasibility constraints on import and export of resources
    n = 'No_export'
    C_meta[n] = ['Prevent some resources from being exported', 0]
    m.addConstrs((grid_export[r,d,h] == 0 
                  for r in ['Gas', 'Wood', 'Diesel']
                  for h in Hours for d in Days), n);
    
    if not Energy_Producer:
        n = 'No_import'
        C_meta[n] = ['Prevent some resources from being imported', 0]
        m.addConstrs((grid_import['BM',d,h] == 0
                      for h in Hours for d in Days), n);
    else:
        n = 'No_import'
        C_meta[n] = ['Prevent some resources from being imported', 0]
        m.addConstrs((grid_import['BM',d,h] + grid_import['Elec',d,h] + grid_import['Gas',d,h] == 0
                      for h in Hours for d in Days), n);
    
    # Prevent simultaneous import and export of electricity
    n = 'grid_import_export_elec'
    C_meta[n] = ['Prevent the sytem to buy and sell EL at the same time', 61]
    m.addConstrs((grid_import_elec[d,h] + grid_export_elec[d,h] <= 1 
                  for d in Days for h in Hours), n);
    n = 'grid_import_elec'
    C_meta[n] = ['M constraint to link IS importing with elec import', 63]
    m.addConstrs((grid_import_elec[d,h]*Bound >= grid_import['Elec',d,h] 
                  for d in Days for h in Hours), n);
    n = 'grid_export_elec'
    C_meta[n] = ['M constraint to link IS exporting with Elec production', 62]
    m.addConstrs((grid_export_elec[d,h]*Bound >= grid_export['Elec',d,h] 
                  for d in Days for h in Hours), n);
    
    # Limit the Elec export in any given time by the production of renewable Elec
    # To prevent the battery from stockpiling and seling everything at peak CO2 cost
    n = 'grid_export_elec_limit'
    U_prod_elec = [u for u in U_res['prod']['Elec'] if u not in ('BAT',)]
    C_meta[n] = ['Limit the export of renewable EL to the renewable EL prod', 60]
    m.addConstrs((grid_export['Elec',d,h] <= 
                  sum(unit_prod[up]['Elec',d,h] for up in U_prod_elec)
                  for d in Days for h in Hours), n);
    
    
    return grid_import_a, grid_export_a, grid_import, grid_export

###############################################################################
### Economic performance indicators
    #   CAPEX 
    #   OPEX 
    #   TOTEX 
###############################################################################

def model_objectives(m, Days, Hours, grid_import_a, grid_export_a, unit_size, 
                     unit_install, unit_capex, grid_import, grid_export):
    # Variable
    n = 'capex'
    V_meta[n] = ['MCHF', 'total CAPEX', 'unique']
    capex = m.addVar(lb=0, ub=Tight, name=n)
    
    n = 'opex'
    V_meta[n] = ['MCHF/year', 'total annual opex', 'unique']
    opex = m.addVar(lb=-Tight, ub=Tight, name=n)
    
    n = 'totex'
    V_meta[n] = ['MCHF/year', 'total annualized expenses', 'unique']
    totex = m.addVar(lb=-Tight, ub=Tight, name=n)
    
    # Constraints
    n = 'Is_installed'
    C_meta[n] = ['M constraint to link IS installed with the installed size', 75]
    m.addConstrs((unit_install[u]*Bound >= unit_size[u] for u in Units), n);
    
    n = 'Is_installed_capex'
    C_meta[n] = ['Additional big-M constraint to eliminate CAPEX error', 76]
    m.addConstrs((unit_install[u]*Tight >= unit_capex[u] for u in Units), n);
    
    n = 'Minimum_size'
    for u in Units:
        C_meta[n + f'[u]'] = [f'Lower limit on installed capacity IF installed', 77]
    m.addConstrs((unit_size[u] >= P[u, 'Min_size']*unit_install[u] for u in Units), n);
    
    n = 'Capex'
    C_meta[n] = ['Unit CAPEX relative to unit size and cost parameters', 78]
    m.addConstrs((unit_capex[u] == P[u,'Cost_multiplier']*
                  (unit_size[u]*P[u,'Cost_per_size'] + 
                   unit_install[u]*P[u,'Cost_per_unit'])*
                  annualize(P[u,'Life'], P['Farm','i'])*1e-3
                  for u in Units), n);
    
    n = 'capex_sum'
    C_meta[n] = ['Sum of the CAPEX of all units', 79]
    m.addConstr(capex == sum(unit_capex[u] for u in Units), n);
    
    n = 'opex_sum'
    C_meta[n] = ['Sum of the OPEX of all resources', 80]
    m.addConstr(opex == sum(grid_import_a[r]*P[r,'Import_cost'] - 
                            grid_export_a[r]*P[r,'Export_cost'] 
                            for r in G_res)/1000 
                        + sum(unit_capex[u]*P[u,'Maintenance']/
                              annualize(P[u,'Life'], P['Farm','i'])
                              for u in Units), n);
    
    n = 'totex_sum'
    C_meta[n] = ['TOTEX relative to the OPEX, the annual CAPEX', 81]
    m.addConstr(totex == opex + capex, n);
    
    # CO2 emissions
    n = 'envex'
    V_meta[n] = ['kt-CO2', 'Annual total CO2 emissions', 'unique']
    envex = m.addVar(lb=-Tight, ub=Tight, name=n)

    n = 'r_envex'
    V_meta[n] = ['t-CO2', 'Annual total CO2 emissions for a given resource', 'unique']
    r_envex = m.addVars(G_res, lb=-Bound, ub=Bound, name=n)
    
    # c = 'Emissions'
    # n = 'Emissions'
    # C_meta[n] = ['Instant CO2 emissions relative to Elec and Gas imports', 0]
    # m.addConstr(emissions == 
    #             (sum((grid_import_a[r] - P['Farm', 'Export_CO2']*grid_export_a[r])
    #                  *P[r,c] for r in G_res) + 
    #             sum(unit_size[u]*P[u,'LCA']/P[u,'Life'] for u in Units))/1000, n);
    
    
    f_CO2 = P['Farm', 'Export_CO2']
    n = 'Elec_envex'
    C_meta[n] = ['Annual CO2 emissions relative to Elec import and export', 83]
    m.addConstr(r_envex['Elec'] == 1e-3*sum(sum(
        Elec_CO2[d,h]*(grid_import['Elec',d,h] - f_CO2*grid_export['Elec',d,h]) 
        for h in Hours)*Frequence[d] for d in Days), n);
    
    for r in [r for r in G_res if r != 'Elec']:
        n=f'{r}_envex'
        C_meta[n] = [f'Annual CO2 emissions relative to {r} import and export', 84]
        m.addConstr(r_envex[r] == P[r,'Emissions']*
                    (grid_import_a[r] - f_CO2*grid_export_a[r]), n);
    
    n='Total_emissions'
    C_meta[n] = ['Instant CO2 emissions relative to Elec and Gas imports', 85]
    m.addConstr(envex == 1e-3*sum(r_envex[r] for r in G_res) +
                1e-3*sum(unit_size[u]*P[u,'LCA']/P[u,'Life'] for u in Units) +
                (1 - P['Physical','Manure_AD']*unit_install['AD'])*
                P['Farm','Biomass_emissions'], n);
    
    C_meta['Limit_envex'] = ['Fix a limit to the emissions, for Pareto only', 0]
    C_meta['Limit_totex'] = ['Fix a limit to the TOTEX, for Pareto only', 0]
    
    return totex, capex, opex, envex


##################################################################################################
### Scenarios
##################################################################################################


def extreme_case(m, unit_size):
    """ Represent an extreme case scenario for which the building heating 
        system has to remain operational. Hypothesis include:
            1. -20C sustained outside temperature (T_ext_min in parameters.csv)
            2. 18C sustained inside temperature (T_min in heat_load_param.csv)
            3. No gains
            4. The WBOI is deactivated - No wood pellets
            5. The AHP is deactivated - Too cold T_ext
            6. The CHP units are deactivated - Maintenace 
            7. No AD heat load
            
        The GBOI, EH and GHP alone have to be big enough to answer this load.
    """

    n='Extreme_case'
    C_meta[n] = ['Extreme scenario, only GBOI, EH and GHP active', 12]
    m.addConstr(Q_extreme == sum(unit_size[u] for u in ['GBOI', 'EH', 'GHP']), n);



##################################################################################################
### Set objective and resolve
##################################################################################################


def set_objective(m, switcher, objective, Limit=None):
    
    print_highlight('Objective: ' + objective)
    set_objective = switcher.get(objective)
    if 'limit' in objective:
        set_objective(Limit)
    else:
        set_objective()


def print_highlight(string):
    print('******************************************************************')
    print('******************* {} **************************'.format(string))
    print('******************************************************************')
    
    
def run(objective, Limit=None, New_Pamar=None, New_Setting=None, Relax=False):
    """ Option to redefine the set of Parameters P and Settings S """
    if type(New_Pamar) != type(None):
        global P
        P = New_Pamar
    if type(New_Setting) != type(None):
        global S
        S = New_Setting
        
    """ Run each function to effectivel build the MILP """
    # Reset old model and creat a new model
    m = initialize_model()
    # Create most variables
    (unit_prod, unit_cons, unit_install, unit_size, unit_capex, unit_SOC, 
     unit_charge, unit_discharge
     ) = variables.declare_vars(m, Bound, V_meta, Days, Hours, Periods)
    # Constrain unit sizes accoring to settings.csv min-max
    cstr_unit_size(m, S, unit_size)
    # Model each unit
    model_units(m, Days, Hours, Periods, unit_prod, unit_cons, unit_size, 
                unit_SOC, unit_charge, unit_discharge, unit_install, P)
    # Model mass and energy balance
    (grid_import_a, grid_export_a, grid_import, grid_export
     ) = model_energy_balance(m, Days, Hours, unit_cons, unit_prod, unit_install)
    # Calculate objective variables
    totex, capex, opex, envex = model_objectives(
        m, Days, Hours, grid_import_a, grid_export_a, unit_size, unit_install, 
        unit_capex, grid_import, grid_export)
    # Constraint for extreme case scenario
    extreme_case(m, unit_size)
    
    print(C_meta)

    """ Definie all possible objective function """
    def minimize_opex():
        m.setObjective(opex, GRB.MINIMIZE)
    def minimize_capex():
        m.setObjective(capex, GRB.MINIMIZE)

    def pareto_constrained_opex(Limit_opex):
        print('-----------------{}--------------------'.format(Limit_opex))
        m.addConstr(opex <= Limit_opex, 'Limit_opex')
        m.setObjective(capex, GRB.MINIMIZE)
    def pareto_constrained_capex(Limit_capex):
        print('-----------------{}--------------------'.format(Limit_capex))
        m.addConstr(capex <= Limit_capex, 'Limit_capex');
        m.setObjective(opex, GRB.MINIMIZE)

    
    def minimize_totex():
        m.setObjective(totex, GRB.MINIMIZE)
    def minimize_envex():
        m.setObjective(envex, GRB.MINIMIZE)
        
    def pareto_constrained_totex(Limit_totex):
        print('-----------------{}--------------------'.format(Limit_totex))
        m.addConstr(totex <= Limit_totex, 'Limit_totex')
        m.setObjective(envex, GRB.MINIMIZE)
    def pareto_constrained_envex(Limit_envex):
        print('-----------------{}--------------------'.format(Limit_envex))
        m.addConstr(envex <= Limit_envex, 'Limit_envex');
        m.setObjective(totex, GRB.MINIMIZE)
        
    def minimize_totex_tax_co2():
        m.setObjective(totex + envex*P['CO2']['Tax'], GRB.MINIMIZE)
        
    switcher = {
        'totex': minimize_totex,
        'envex': minimize_envex,
        'limit_totex': pareto_constrained_totex,
        'limit_envex': pareto_constrained_envex,

        'opex': minimize_opex,
        'capex': minimize_capex,
        'limit_opex': pareto_constrained_opex,
        'limit_capex': pareto_constrained_capex,
        
        'totex_tax_co2': minimize_totex_tax_co2,
        }
    
    set_objective(m, switcher, objective, Limit=Limit)
    m.setParam("Presolve", 2)
    m.setParam("NumericFocus", 2)
    m.optimize()
    
    
    
    if Relax:
        # Relaxion in case of infeasible model
        if m.status == GRB.INFEASIBLE:
            print_highlight('Model INFEASIBLE!!!')
            
        if m.status == GRB.INFEASIBLE and Relax:
            m.feasRelaxS(1, False, False, True)
            m.optimize()
            print_highlight('Model INFEASIBLE!!!')  
    
    return m

##################################################################################################
### END
##################################################################################################





