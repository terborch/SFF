# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 13:59:35 2020

@author: smith
"""


"""
Cost vs Gains of installing a 6kW SOFC on the existing biogas installation of Palézieux
"""
import numpy as np
import data

P, _ = data.get_param('parameters.csv')
P_eco, _ = data.get_param('cost_param.csv')
P = P.append(P_eco)

t_op = 8334 # Hours per year
size, capex = {}, {}
size['SOFC'] = 6 # kW electric installed capacity
size['GCSOFC'] = size['SOFC']/P['SOFC', 'Eff_elec']

Eff_GCSOFC = P['GCSOFC', 'Elec_cons']*P['SOFC', 'Eff_elec']     #kW_el/kW_biogas
Biogas_cons = size['SOFC']/P['SOFC', 'Eff_elec']*t_op/1000      #MWh/an

SOFC_eff = np.array([0.5, 0.55]) #Electric efficience low estimate, high estimate
Elec_eff = {'SOFC': SOFC_eff*(1 - P['GCSOFC', 'Elec_cons']), 'ICE': 0.372}
Elec_prod = {}
for u in ['SOFC', 'ICE']:
    Elec_prod[u] = Biogas_cons*Elec_eff[u]         #MWh/an

totex = {}
size['ICE'] = 6
for u in ['SOFC', 'GCSOFC', 'ICE']:
    capex[u] = (P[u, 'Cost_per_size']*size[u] + P[u, 'Cost_per_unit']
             )*P[u, 'Cost_multiplier']
    totex[u] = capex[u]*(data.annualize(P[u, 'Life'], P['Farm', 'i']) + 
                         P[u, 'Maintenance'])

# Elec cost per kwh
    # current
totex['ICE']/Elec_prod['ICE']
    # deviate 12kW of biogas
(totex['SOFC'] + totex['GCSOFC'])/(Elec_prod['SOFC'] - Elec_prod['ICE'])
    # Add 12kW of biogas output
(totex['SOFC'] + totex['GCSOFC'])/Elec_prod['SOFC']