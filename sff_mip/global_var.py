"""
### Variable declaration
    #   unit_prod - dict of vars - What each unit produce of consume during one time period
    #   unit_size - vars - The size of each unit
    #   unit_install - vars - Whether or not each unit is installed
    #   unit_capex - vars - capex of each unit
    #   TODO: Add V_meta metadata ###V_meta['unit_prod[{}]'.format(u)]
"""

# External modules
from gurobipy import GRB
# Internal modules
from initialize_model import m, Bound, Periods, V_meta
from global_set import Units, Units_prod, Units_cons


# Unit production and consumption of each resource during one period
# Variable format : unit_prod['PV'][('Elec',0)]
# Result format : prod[PV][Elec,0]
unit_prod, unit_cons = {}, {}
for u in Units:
    if u in Units_prod:
        unit_prod[u] = m.addVars(Units_prod[u], Periods, lb = 0, ub = Bound, name='prod[{}]'.format(u))
    if u in Units_cons:
        unit_cons[u] = m.addVars(Units_cons[u], Periods, lb = 0, ub = Bound, name='cons[{}]'.format(u))

# Size of the installed unit
unit_size = m.addVars(Units, lb = 0, ub = Bound, name='size')

# Whether or not the unit is installed
unit_install = m.addVars(Units, vtype=GRB.BINARY, name='install')

# CAPEX of the installed unit
unit_capex = m.addVars(Units, lb = 0, ub = Bound, name='capex')

# Temperature of a unit
unit_T = {}
V_meta['unit_T[AD]'] = ['°C', 'Interior temperature of the AD']
unit_T['AD'] = m.addVars(Periods + [Periods[-1] + 1], lb=-100, ub=100, name='unit_T[AD]')


### Temporary
Water_flows = ['m1', 'm2', 'm3']
o = 'water_flow_t'
flow_t = m.addVars(Water_flows, Periods, lb=0, ub=Bound, name= o)