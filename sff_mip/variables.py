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

# External modules
from gurobipy import GRB
# Internal modules
from global_set import (Units, U_prod, U_cons, Units_storage, G_res, Resources)

        
def time_steps(*args):
    """ Returns the three different time discretisations used for variable declaration """
    if len(args) == 2:
        Days, Hours = args[0], args[1]
        return Days, Hours
    if len(args) == 1:
        Periods = args[0]
        return (Periods,)

def extend(*args):
    *Time_periods, Smallest_time_period = args
    Smallest_time_period_extended = Smallest_time_period + [Smallest_time_period[-1] + 1]
    if Time_periods:
        return Time_periods[0], Smallest_time_period_extended
    else:
        return (Smallest_time_period_extended,)
        
def declare_vars(m, Bound, V_meta, Days, Hours, Periods):
    Time_steps = {'Daily': time_steps(Days, Hours), 
                  'Annual': time_steps(Periods)}
    # Unit production and consumption of each resource during one period
    # Variable format : unit_prod['PV'][('Elec',0)]
    # Result format : prod[PV][Elec,0]
    unit_prod, unit_cons = {}, {}
    for u in Units:
        Time_periods = Time_steps['Daily']
        if u in U_prod:
            n = f'unit_prod[{u}]'
            for r in U_prod[u]:
                V_meta[n + f'[{r}]'] = ['kW', f'{r} produced by {u}', 'time']
            unit_prod[u] = m.addVars(U_prod[u], *Time_periods, lb=0, ub=Bound, name=n)
        if u in U_cons:
            n = f'unit_cons[{u}]'
            for r in U_cons[u]:
                V_meta[n + f'[{r}]'] = ['kW', f'{r} consumed by {u}', 'time']
            unit_cons[u] = m.addVars(U_cons[u], *Time_periods, lb=0, ub=Bound, name=n)
    
    # Size of the installed unit
    n = 'unit_size'
    for u in Units:
        var_units = ('kW' if u not in Units_storage else 'kWh')
        V_meta[n + f'[{u}]'] = [var_units, f'Installed capacity of {u}', 'unique']
    unit_size = m.addVars(Units, lb=0, ub=Bound, name=n)
    
    # Whether or not the unit is installed
    n = 'unit_install'
    for u in Units:
        V_meta[n + f'[{u}]'] = ['-', f'{u} decision variable', 'bool']
    unit_install = m.addVars(Units, vtype=GRB.BINARY, name=n)
    
    # CAPEX of the installed unit
    n = 'unit_capex'
    for u in Units:
        V_meta[n + f'[{u}]'] = ['kCHF', f'Investment cost of {u}', 'unique']
    unit_capex = m.addVars(Units, lb=0, ub=Bound, name=n)
    
    # Storga unit dict of variables                   
    unit_SOC, unit_charge, unit_discharge = {}, {}, {}
    for u in Units_storage:
        Time_periods = Time_steps['Annual']
        n = f'unit_SOC[{u}]'
        V_meta[n] = ['kWh', f'State of charge of {u}', 'time']
        unit_SOC[u] = m.addVars(*extend(*Time_periods), lb=0, ub=Bound, name=n)
        Time_periods = Time_steps['Daily']
        n = f'unit_charge[{u}]'
        V_meta[n] = ['kWh', f'Wheter {u} is charging or not', 'bool']
        unit_charge[u] = m.addVars(*Time_periods, vtype=GRB.BINARY, name=n)
        n = f'unit_discharge[{u}]'
        V_meta[n] = ['kWh', f'Wheter {u} is discharging or not', 'bool']
        unit_discharge[u] = m.addVars(*Time_periods, vtype=GRB.BINARY, name=n)

    # # Resource Variables grid['import_a']['Elec']    
    # grid = {}
    # for g in ['export', 'import']:
    #     for t in ['instant', 'annual']:
    #         u = 'kW' if t=='instant' else 'MWh'
    #         a = '' if t=='instant' else f'_a'
    #         Type = 'time' if t=='instant' else 'unique'
    #         Description = 'purchased by' if t=='import' else 'sold by'
    #         n = f'grid_{g}{a}'
    #         p = (Resources, Days, Hours) if t=='instant' else (Resources)
    #         V_meta[n] = [u, f'{t} resource {Description} by the Farm', Type]
    #         grid[n] = m.addVars(*p, lb=0, ub=Bound, name=n)
    
    return (unit_prod, unit_cons, unit_install, unit_size, unit_capex, 
            unit_SOC, unit_charge, unit_discharge)



###############################################################################
### END
###############################################################################

# PV_prod = m.addVars(['Elec'], Days, Hours, lb=0, ub=Bound, name='PV_prod');

# # Heat consuming units and building
# n='build_cons_Heat'
# V_meta[n] = ['kW', 'Heat consumed by the building', 'time']
# build_cons_Heat = m.addVars(Days, Hours, lb=0, ub=Bound, name=n)

# # Temperature of a unit
# unit_T = {}
# u = 'AD'
# n = f'unit_T[{u}]'
# V_meta[n] = ['°C', f'Temperature in the {u}', 'time']
# unit_T[u] = m.addVars(Days, Hours + [Hours[-1] + 1], lb=-Bound, ub=Bound, name=n)