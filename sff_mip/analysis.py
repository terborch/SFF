# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 10:22:48 2020

@author: nils ter-borch
"""

# import numpy as np
# import os
# import results

# path = os.path.join('inputs', 'inputs.h5')
# Build_dic = results.get_hdf(path)
# Build_cons = {}
# Build_cons['Elec'] = Build_dic['Build_cons_Elec'].values
# Build_cons['Heat'] = Build_dic['build_Q'].values
# Peak_Heat_load = np.max(Build_cons['Heat'])


import data

cost, _ = data.get_param('cost_param.csv')

perf, _ = data.get_param('parameters.csv')


def heat_cost(u, size):
    opex = (cost['Gas', 'Import_cost']/perf[u, 'Eff']
            )*perf['Farm', 'cons_Heat_annual']
    capex = cost[u, 'Cost_multiplier']*(
        size*cost[u, 'Cost_per_size'] + cost[u, 'Cost_per_unit'])
    tau = data.annualize(cost[u, 'Life'], perf['Farm']['i'])
    
    return opex + capex*tau

heat_cost('GBOI', 845)

heat_cost()