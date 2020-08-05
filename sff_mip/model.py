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
                         Elec_CO2)
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
                unit_SOC, unit_charge, unit_discharge, unit_install):
    
    u = 'GBOI'
    units.gboi(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u])
    
    u = 'WBOI'
    units.wboi(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u])
    
    u = 'AHP'
    units.ahp(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u])
    
    u = 'GHP'
    units.ghp(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u])
    
    u='EH'
    units.eh(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u])
    
    u = 'PV'
    units.pv(m, Days, Hours, unit_prod[u], unit_size[u], Irradiance)
    
    u = 'AD'
    units.ad(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], 
             AD_cons_Heat, unit_install[u])
    
    u = 'SOFC'
    units.sofc(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u])
    
    u = 'ICE'
    units.ice(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u])
    
    u = 'BAT'
    units.bat(m, Periods, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], 
              unit_SOC[u], unit_charge[u], unit_discharge[u], unit_install[u])
    
    u = 'CGT'
    units.cgt(m, Periods, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], 
              unit_SOC[u], unit_charge[u], unit_discharge[u], unit_install[u])
    
    u = 'BS'
    units.bs(m, Periods, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], 
              unit_SOC[u], unit_charge[u], unit_discharge[u], unit_install[u])
    
    u = 'GCSOFC'
    units.gcsofc(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u])
    
    u = 'BU'
    units.bu(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u])
    
    u = 'GFS'
    units.gfs(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u], U_prod[u])
    
    u = 'GI'
    units.gi(m, Days, Hours, unit_prod[u], unit_cons[u], unit_size[u])
    


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
    
    n = 'No_import'
    C_meta[n] = ['Prevent some resources from being imported', 0]
    m.addConstrs((grid_import['BM',d,h] == 0
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
    capex = m.addVar(lb=-Tight, ub=Tight, name=n)
    
    n = 'opex'
    V_meta[n] = ['MCHF/year', 'total annual opex', 'unique']
    opex = m.addVar(lb=0, ub=Tight, name=n)
    
    n = 'totex'
    V_meta[n] = ['MCHF/year', 'total annualized expenses', 'unique']
    totex = m.addVar(lb=0, ub=Tight, name=n)
    
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
                  annualize(P[u,'Life'], P['Farm','i'])/1000
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
    V_meta[n] = ['kt-CO2', 'Annual total CO2 emissions for a given resource', 'unique']
    r_envex = m.addVars(G_res, lb=-Tight, ub=Tight, name=n)
    
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
    m.addConstr(r_envex['Elec'] == 1e-6*sum(sum(
        Elec_CO2[d,h]*(grid_import['Elec',d,h] - f_CO2*grid_export['Elec',d,h]) 
        for h in Hours)*Frequence[d] for d in Days), n);
    
    for r in [r for r in G_res if r != 'Elec']:
        n=f'{r}_envex'
        C_meta[n] = [f'Annual CO2 emissions relative to {r} import and export', 84]
        m.addConstr(r_envex[r] == 1e-3*P[r,'Emissions']*
                    (grid_import_a[r] - f_CO2*grid_export_a[r]), n);
    
    n='Total_emissions'
    C_meta[n] = ['Instant CO2 emissions relative to Elec and Gas imports', 85]
    m.addConstr(envex == sum(r_envex[r] for r in G_res) +
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
    
    P, _ = get_param('heat_load_param.csv')

    b = 'build'
    n='Extreme_case'
    C_meta[n] = ['Extreme scenario, only GBOI, EH and GHP active', 12]
    m.addConstr(P[b, 'Heated_area']*P[b, 'U_b']*
                (P[b, 'T_min'] - P[b, 'T_ext_extreme']) ==
                sum(unit_size[u] for u in ['GBOI', 'EH', 'GHP']), n);



##################################################################################################
### Set objective and resolve
##################################################################################################


def set_objective(m, switcher, objective, Limit=None, relax=False):
    
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
    
    
def run(objective, Limit=None, New_Pamar=None, New_Setting=None, relax=False):
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
                unit_SOC, unit_charge, unit_discharge, unit_install)
    # Model mass and energy balance
    (grid_import_a, grid_export_a, grid_import, grid_export
     ) = model_energy_balance(m, Days, Hours, unit_cons, unit_prod, unit_install)
    # Calculate objective variables
    totex, capex, opex, envex = model_objectives(
        m, Days, Hours, grid_import_a, grid_export_a, unit_size, unit_install, 
        unit_capex, grid_import, grid_export)
    # Constraint for extreme case scenario
    extreme_case(m, unit_size)

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
    
    set_objective(m, switcher, objective, Limit=Limit, relax=False)
    m.optimize()
    
    if relax:
        # Relaxion in case of infeasible model
        if m.status == GRB.INFEASIBLE:
            print_highlight('Model INFEASIBLE!!!')
            
        if m.status == GRB.INFEASIBLE and relax:
            m.feasRelaxS(1, False, False, True)
            m.optimize()
            print_highlight('Model INFEASIBLE!!!')  
    
    return m

##################################################################################################
### END
##################################################################################################

def get_expr_coos(expr, var_indices):
    for i in range(expr.size()):
        dvar = expr.getVar(i)
        yield expr.getCoeff(i), var_indices[dvar]
    
def get_matrix_coos(m):
    dvars = m.getVars()
    constrs = m.getConstrs()
    var_indices = {v: i for i, v in enumerate(dvars)}
    for row_idx, constr in enumerate(constrs):
        for coeff, col_idx in get_expr_coos(m.getRow(constr), var_indices):
            yield row_idx, col_idx, coeff

def funky(m):
    import pandas as pd
    dvars = m.getVars()
    constrs = m.getConstrs()
    
    obj_coeffs = m.getAttr('Obj', dvars)
    
    var_index = {v: i for i, v in enumerate(dvars)}
    constr_index= {c: i for i, c in enumerate(constrs)}

    
    nzs = pd.DataFrame(get_matrix_coos(m), columns=['row_idx', 'col_idx', 'coeff'])
    return nzs






"""
    # l - 145
    n = 'Building_T_daily_cycle'
    C_meta[n] = ['Cycling constraint to carry over the temperature from one day to the next', 0]
    m.addConstrs((build_T[d,0] == build_T[d,Hours[-1] + 1] for d in Days[:-1]), n);
    n = 'Building_T_yearly_cycle'
    C_meta[n] = ['Carry over the temperature from one modelling period to the next', 0]
    m.addConstr((build_T[0,0] == build_T[Days[-1],Hours[-1] + 1]), n);
"""

###############################################################################
### OLD - Heat cascade with water volume flows
###############################################################################

""" 
def model_heating(m, Days, Hours, unit_cons, unit_prod, build_cons_Heat, v, unit_install):
    g = 'General'
    n = 'Heat_load_balance_AD'
    C_meta[n] = ['Heat consumed by the AD relative to hot water supply and temperature delta', 0]
    m.addConstrs((unit_cons['AD']['Heat',d,h] == P[g]['Cp_water']*(P['AD']['Th'] - P['AD']['Tc'])*
                  (v['GBOI']['AD',d,h] + v['SOFC']['AD',d,h]) for d in Days for h in Hours), n);
    
    n = 'Heat_load_balance_build'
    C_meta[n] = ['Heat consumed by the Building relative to hot water supply and temperature delta', 0]
    m.addConstrs((build_cons_Heat[d,h] == P[g]['Cp_water']*(P['build']['Th'] - P['build']['Tc'])*
                  (v['GBOI']['build',d,h] + v['SOFC']['build',d,h]) for d in Days for h in Hours), n);
    
    n = 'Heat_load_balance_heat_prod'
    C_meta[n] = ['Heat produced by each unit relative to hot water supplied and temperature delta', 0]
    m.addConstrs((unit_prod[u]['Heat',d,h] == 
                  P[g]['Cp_water']*(v[u]['build',d,h]*(P['build']['Th'] - P['build']['Tc']) + 
                                 v[u]['AD',d,h]*(P['AD']['Th'] - P['AD']['Tc'])) 
                  for u in Heat_prod for d in Days for h in Hours), n);
    
"""


###############################################################################
### OLD - Farm thermodynamic model
###############################################################################

"""
def next_day(d):
    if not d == Days[-1]:
        return d+1
    else:
        return 0

# Farm temperature
penalty = model_farm_temperature(m, Days, Hours, Ext_T, Irradiance, build_cons_Heat)

def model_farm_temperature(m, Days, Hours, Ext_T, Irradiance, build_cons_Heat):
    c = 'build'
    n = 'build_T'
    V_meta[n] = ['°C', 'Interior temperature of the building', 'time']
    build_T = m.addVars(Days, Hours + [Hours[-1] + 1], lb=-Bound, ub=Bound, name=n)
    
    P_meta[c]['Gains_ppl'] = ['kW/m^2', 'Heat gains from people', 'calc']
    C_meta['Gains_ppl'] = ['Building people gains', 4, 'P']
    Gains_ppl = annual_to_daily(P[c]['Gains_ppl'], df_cons['Gains'].values)

    P_meta[c]['Gains_elec'] = ['kW/m^2', 'Heat gains from appliances', 'calc']
    C_meta['Gains_elec'] = ['Building electric gains', 3, 'P']
    Gains_elec = P[c]['Elec_heat_frac'] * Build_cons_Elec / Heated_area

    P_meta[c]['Gains_solar'] = ['kW/m^2', 'Heat gains from irradiation', 'calc']
    C_meta['Gains_solar'] = ['Building solar gains', 3, 'P']
    Gains_solar = P[c]['Building_absorptance'] * Irradiance
    
    P_meta[c]['Gains'] = ['kW/m^2', 'Sum of all heat gains', 'calc']
    C_meta['Gains'] = ['Sum of all building heating gains', 3, 'P']
    Gains = Gains_ppl + Gains_elec + Gains_solar
    
    n = 'Building_temperature'
    C_meta[n] = ['Building Temperature change relative to External Temperature, Gains and Losses', 2]
    m.addConstrs((
        P[c]['C_b']*(build_T[d,h+1] - build_T[d,h]) == 
        P[c]['U_b']*(Ext_T[d,h] - build_T[d,h]) + Gains[d,h] + 
        build_cons_Heat[d,h]/Heated_area for d in Days for h in Hours), n);

    n = 'Building_T_daily_cycle'
    C_meta[n] = ['Cycling constraint for building temperature', 0]
    m.addConstrs((build_T[d,Hours[-1] + 1] == build_T[next_day(d), 0] for d in Days), n);
    n = 'Building_T_daily_init'
    C_meta[n] = ['Fix the initial building temperature every day', 0]
    m.addConstrs((build_T[d,0] ==  build_T[d,0] for d in Days), n);
    
    n = 'Building_temperature_min'
    C_meta[n] = ['Lower limit on Building Temperature', 0]
    m.addConstrs((build_T[d,h] >= P[c]['T_min'] for d in Days for h in Hours), n);
    C_meta[n] = ['Upper limit on Building Temperature', 0]
    n = 'Building_temperature_max'
    m.addConstrs((build_T[d,h] <= P[c]['T_max'] for d in Days for h in Hours), n);
    
    n = 'penalty'
    V_meta[n] = ['MCHF', 'Isntant Penalty for deviating from the comfort temperature', 'time']
    penalty = m.addVars(Days, Hours, lb=0, ub=Bound, name=n)
    n = 'penalty_a'
    V_meta[n] = ['MCHF', 'Sum of Penalty for deviating from the comfort temperature', 'unique']
    penalty_a = m.addVar(lb=0, ub=Bound, name=n)
    
    n = 'comfort_delta_T'
    V_meta[n] = ['°C', 'Temerature difference between comfort and actual building temperature', 'time']
    delta_T_1 = m.addVars(Days, Hours, lb=-Bound, ub=Bound, name=n)
    n = 'Comfort_delta_T'
    C_meta[n] = ['Temerature difference between comfort and actual building temperature', 0]
    m.addConstrs((delta_T_1[d,h] == P[c]['T_amb'] - build_T[d,h] for d in Days for h in Hours), n);
    
    n = 'comfort_delta_T_abs'
    V_meta[n] = ['°C', 'Absolute Temerature difference between comfort and actual building temperature',
                 'time']
    delta_T_abs = m.addVars(Days, Hours, lb=0, ub=Bound, name=n)
    n = 'Comfort_delta_T_abs'
    C_meta[n] = ['Absolute Temerature difference between comfort and actual building temperature', 'time', 0]
    m.addConstrs((delta_T_abs[d,h] == gp.abs_(delta_T_1[d,h]) for d in Days for h in Hours), n);
    
    n = 'comfort_T_penalty'
    C_meta[n] = ['Instant penalty value relative to temperature difference and penalty factor', 0]
    m.addConstrs((penalty[d,h] == delta_T_abs[d,h]*3.3013330297486014e-05 for d in Days for h in Hours), n);
    
    n = 'comfort_T_penalty_tot'
    C_meta[n] = ['Sum of penalty value relative to instant penalty', 0]
    m.addConstr(penalty_a == penalty.sum('*'), n);
    
    return penalty


"""