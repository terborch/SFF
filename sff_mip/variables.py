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
from global_set import Units, U_prod, U_cons, Units_storage, Heat_cons, Heat_prod

def declare_vars(m, Bound, Periods, V_meta):
    # Unit production and consumption of each resource during one period
    # Variable format : unit_prod['PV'][('Elec',0)]
    # Result format : prod[PV][Elec,0]
    unit_prod, unit_cons = {}, {}
    for u in Units:
        if u in U_prod:
            n = f'unit_prod[{u}]'
            for r in U_prod[u]:
                V_meta[n + f'[{r}]'] = ['kW', f'{r} produced by {u}', 'time']
            unit_prod[u] = m.addVars(U_prod[u], Periods, lb=0, ub=Bound, name=n)
        if u in U_cons:
            n = f'unit_cons[{u}]'
            for r in U_cons[u]:
                V_meta[n + f'[{r}]'] = ['kW', f'{r} consumed by {u}', 'time']
            unit_cons[u] = m.addVars(U_cons[u], Periods, lb=0, ub=Bound, name=n)
    
    # Size of the installed unit
    n = 'unit_size'
    for u in Units:
        var_units = ('kW' if u not in Units_storage else 'kWh')
        V_meta[n + f'[{u}]'] = [var_units, f'Installed capacity of {u}', 'unique']
    unit_size = m.addVars(Units, lb = 0, ub = Bound*10, name=n)
    
    # Whether or not the unit is installed
    n = 'unit_install'
    for u in Units:
        V_meta[n + f'[{u}]'] = ['-', f'{u} decision variable', 'bool']
    unit_install = m.addVars(Units, vtype=GRB.BINARY, name=n)
    
    # CAPEX of the installed unit
    n = 'unit_capex'
    for u in Units:
        V_meta[n + f'[{u}]'] = ['kCHF', f'Investment cost of {u}', 'unique']
    unit_capex = m.addVars(Units, lb = 0, ub = Bound, name=n)
    
    # Storga unit dict of variables
    unit_SOC, unit_charge, unit_discharge = {}, {}, {}
    for u in Units_storage:
        n = f'unit_SOC[{u}]'
        V_meta[n] = ['kWh', f'State of charge of {u}', 'time']
        unit_SOC[u] = m.addVars(Periods + [Periods[-1] + 1], lb=0, ub=Bound, name=n)
        V_meta[f'unit_SOC[{u}]'] = ['kWh', f'State of charge of {u}', 'bool']
        unit_charge[u] = m.addVars(Periods, vtype=GRB.BINARY, name=n)
        V_meta[f'unit_SOC[{u}]'] = ['kWh', f'State of charge of {u}', 'bool']
        unit_discharge[u] = m.addVars(Periods, vtype=GRB.BINARY, name=n)
    
    # Temperature of a unit
    unit_T = {}
    u = 'AD'
    n = f'unit_T[{u}]'
    V_meta[n] = ['°C', f'Temperature in the {u}', 'time']
    unit_T[u] = m.addVars(Periods + [Periods[-1] + 1], lb=-Bound, ub=Bound, name=n)
    
    # Heat consuming units and building
    n='build_cons_Heat'
    V_meta[n] = ['kW', 'Heat consumed by the building', 'time']
    build_cons_Heat = m.addVars(Periods, lb=0, ub=Bound, name=n)
    
    # Volum flows of water transporting heat in m^3
    v = {}
    for u in Heat_prod:
        n = f'v[{u}]'
        for b in Heat_cons:
            V_meta[n + f'[{b}]'] = ['m^3/h', 'Volume flow of heating water', 'time']
        v[u] = m.addVars(Heat_cons, Periods, lb=0, ub=Bound, name=n)
    
                    
    return (unit_prod, unit_cons, unit_install, unit_size, unit_capex, unit_T, build_cons_Heat, unit_SOC, 
     unit_charge, unit_discharge, v)