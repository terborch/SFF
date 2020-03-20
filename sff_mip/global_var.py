"""
### Variable declaration
    #   unit_prod_t - dict of vars - What each unit produce of consume during one time period
    #   unit_size - vars - The size of each unit
    #   unit_install - vars - Whether or not each unit is installed
    #   u_CAPEX - vars - capex of each unit
"""

# External modules
from gurobipy import GRB
# Internal modules
from initialize_model import m, Bound
from global_set import Units, Units_prod, Units_cons, Periods


# Unit production and consumption of each resource during one period
# Variable format : unit_prod_t['PV'][('Elec',0)]
# Result format : PV_prod_t[Elec,0]
# Result format details: <unit>_<pord or cons>_t[<resource>,<period>]
unit_prod_t, unit_cons_t = {}, {}
for u in Units:
    if u in Units_prod:
        unit_prod_t[u] = m.addVars(Units_prod[u], Periods, lb = 0, ub = Bound, name= u + "_prod_t")
    if u in Units_cons:
        unit_cons_t[u] = m.addVars(Units_cons[u], Periods, lb = 0, ub = Bound, name= u + "_cons_t")

# Size of the installed unit
unit_size = m.addVars(Units, lb = 0, ub = Bound, name="size")

# Whether or not the unit is installed
unit_install = m.addVars(Units, vtype=GRB.BINARY, name="install")

# CAPEX of the installed unit
u_CAPEX = m.addVars(Units, lb = 0, ub = Bound, name="CAPEX")

