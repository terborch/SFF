# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 10:22:48 2020

@author: nils ter-borch
"""

import numpy as np
import os
import results

path = os.path.join('inputs', 'inputs.h5')
Build_dic = results.get_hdf(path)
Build_cons, Peak_load = {}, {}
Build_cons['Elec'] = Build_dic['Build_cons_Elec'].values
Build_cons['Heat'] = Build_dic['build_Q'].values
Peak_load['Heat'] = np.max(Build_cons['Heat'])
Peak_load['Elec'] = np.max(Build_cons['Elec'])

from global_set import Units, U_cons
import data
import plot
import results
    
cost, _ = data.get_param('cost_param.csv')

perf, _ = data.get_param('parameters.csv')


def heat_cost(u, size):
    Eff = perf[u, 'COP'] if u == 'AHP' else perf[u, 'Eff']
    opex = (cost[U_cons[u][0], 'Import_cost']/Eff
            )*perf['Farm', 'cons_Heat_annual']
    capex = cost[u, 'Cost_multiplier']*(
        size*cost[u, 'Cost_per_size'] + cost[u, 'Cost_per_unit'])
    tau = data.annualize(cost[u, 'Life'], perf['Farm']['i'])
    
    return ((opex + capex*tau)/perf['Farm', 'cons_Heat_annual'],    # kCHF/kWh-heat
            (capex*tau)/(capex*tau + opex),                         # percent capex
            0)                                                      # kWh electricity




costs={}
for u in ['GBOI', 'EH', 'WBOI', 'AHP']:
    costs[u] = heat_cost(u, Peak_load['Heat'])


def cogen_cost(u, size):
    opex = (cost[U_cons[u][0], 'Import_cost']/(
        (1 - perf[u, 'Eff_elec'])*perf[u, 'Eff_thermal'])
                    )*perf['Farm', 'cons_Heat_annual']
    capex = cost[u, 'Cost_multiplier']*(
        size*cost[u, 'Cost_per_size'] + cost[u, 'Cost_per_unit'])
    tau = data.annualize(cost[u, 'Life'], perf['Farm']['i'])
    
    return ((opex + capex*tau)/perf['Farm', 'cons_Heat_annual'],    # kCHF/kWh-heat
            (capex*tau)/(capex*tau + opex),                         # percent capex
            perf['Farm', 'cons_Heat_annual']*                       # kWh electricity
            perf[u, 'Eff_elec']/((1 - perf[u, 'Eff_elec'])*perf[u, 'Eff_thermal'])
             )  

for u in ['SOFC', 'ICE']:
    costs[u] = cogen_cost(u, Peak_load['Elec'])



print(costs)


# for u in Units:
#     data.change_settings(u, 'max_capacity', 0)

# size={}
# for u in ['GBOI', 'EH', 'WBOI']:
#     data.change_settings(u, 'max_capacity', 1000)
#     import run
#     path = run.run('totex', Plot=False, Summary=False)
#     df = results.get_hdf(path, 'single')
#     df = df.set_index('Var_name')['Value']
#     size[u] = df[f'unit_size[{u}]']
#     data.change_settings(u, 'max_capacity', 0)


