# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 16:37:47 2020

@author: smith
"""


"""
A tiny program to write parameters into Latex table format
"""
import os
import pandas as pd
import data
from global_set import Units, Resources, G_res

P, P_meta = data.get_param('parameters.csv')
P_heat, P_heat_meta = data.get_param('heat_load_param.csv')
P_eco, P_eco_meta = data.get_param('cost_param.csv')


# ### Palezieux parameters injection
# P , _ = data.get_all_param()
# P_heat_load, _ = data.get_param('heat_load_param.csv')
# P = P.append(P_heat_load)
# P_new, _ = data.get_param('palezieux_param.csv')

# # Parma pre-calculation
#  # Inside write_inputs => calc_param.csv
# f = 'Farm'
# P[f, 'cons_Elec_annual'] = 1e3*P_new[f, 'cons_Elec_annual']
# P[f, 'cons_Heat_annual'] = 1e3*(P_new[f, 'cons_heat'] + P_new[f, 'export_heat'])
# P[f, 'Biomass_prod'] = 1e6*P_new[f, 'Biomass']/8760
# A, _ = data.get_param('animals.csv')
# P[f, 'Biomass_emissions'] = 1e-6*(P_new[f, 'Cows']*
#     A['Dairy_cows', 'Manure']*P['Physical', 'Manure_emissions'])
#  # Inside heal_loads_cals => heat_load_param.csv
# P['AD', 'LSU'] = P_new[f, 'Cows']
# P['build', 'Heated_area'] = P_new[f, 'A_heated']

# # Remaining Parameters
#  # Inside parameters.csv
# u = 'AD'
# P[u, 'Heat_cons'] = P_new[u, 'cons_heat']
# P[u, 'Elec_cons'] = P_new[u, 'cons_elec']
# P_eco[u, 'Cost_multiplier'] = 1
# P_eco[u, 'Cost_per_size'] = 1e3*0.9*P_new[u, 'cost_inv']/P_new[u, 'Capacity']
# P_eco[u, 'Cost_per_unit'] = 1e3*0.1*P_new[u, 'cost_inv']
# P_eco[u, 'Min_size'] = 100
# P_eco[u, 'Ref_size'] = P_new[u, 'Capacity']  

# u = 'ICE'
# P[u, 'Eff_elec'] = P_new[u, 'Eff_elec']
# P[u, 'Eff_thermal'] = P_new[u, 'Eff_thermal']
# P_eco[u, 'Cost_per_size'] = 0.9*P_new[u, 'cost_inv']/P_new[u, 'Capacity']
# P_eco[u, 'Cost_per_unit'] = 0.1*P_new[u, 'cost_inv']
# P_eco[u, 'Maintenance'] = P_new[u, 'cost_maint_net']/P_new[u, 'cost_inv']
# P_eco[u, 'Min_size'] = int(P_new[u, 'Capacity']/3)
# P_eco[u, 'Ref_size'] = P_new[u, 'Capacity']

# u = 'PV'
# P[u, 'max_utilisation'] = 1
# P['Farm', 'Ground_area'] = P_new['Farm', 'A_ground']
# P_eco[u, 'Cost_multiplier'] = 1
# P_eco[u, 'Cost_per_size'] = 0.9*P_new[u, 'cost_inv']/P_new[u, 'Capacity']
# P_eco[u, 'Cost_per_unit'] = 0.1*P_new[u, 'cost_inv']
# P_eco[u, 'Min_size'] = 100
# P_eco[u, 'Ref_size'] = P_new[u, 'Capacity']



# Standard symbols for cost parameter
Symbols = {
'Cost_multiplier':  'c^{mult}',
'Cost_per_size':    'c^{size}',
'Cost_per_unit':    'c^{fixe}',
'LCA':              'm^{LCA}_{CO_2',
'Life':             'n',
'Maintenance':      'c^{maint}',
'Min_size':         'S^{min}',
'Ref_size':         'S^{ref}'
}

Names = {
'Cost_multiplier':  'Cost multiplier',
'Cost_per_size':    'Specific investment cost',
'Cost_per_unit':    'Fixed investment cost',
'LCA':              'LCA emissions',
'Life':             'Life',
'Maintenance':      'Maintenance',
'Min_size':         'Smallest size',
'Ref_size':         'Reference size'
}

SymbolsR = {
'Import_cost':      'c^{buy}',
'Export_cost':      'c^{sell}',
'Emissions':        'm^{buy}_{CO_2'
}

NamesR = {
'Import_cost':      'Purchase cost',
'Export_cost':      'Selling price',
'Emissions':        'Associated emissions'
}

df = P_meta
df['Value'] = P
df.drop(columns=['doi'], inplace=True)

df3 = P_heat_meta
df3['Value'] = P_heat

df = pd.concat([df, df3])

df2 = P_eco_meta.copy()
df2['Value'] = P_eco.copy()

df2['Symbol'] = ""

df2['Latex_symbol'] = ""
df2['Latex_name'] = ""

for u in Units:
    for name in Symbols.keys():
        if name != 'LCA':
            df2.loc[(u, name), 'Latex_symbol'] = '$'+Symbols[name] + '_u'+'$'
        else:
            df2.loc[(u, name), 'Latex_symbol'] = '$'+Symbols[name] + ',u}'+'$'
        df2.loc[(u, name), 'Latex_name'] = Names[name]

for r in G_res:
    for name in SymbolsR.keys():
        if name != 'Emissions':
            df2.loc[(r, name), 'Latex_symbol'] = '$'+SymbolsR[name] + '_{'+r+'}'+'$'
        else:
            df2.loc[(r, name), 'Latex_symbol'] = '$'+SymbolsR[name] + '\,'+r+'}'+'$'
        df2.loc[(r, name), 'Latex_name'] = NamesR[name]
 
def latex_value(p):
    try:
        val = '{:0.6f}'.format(p).rstrip('0').rstrip('.')
        return f'${val}$'
    except:
        pass
    
def latex_units(u):
    if '%CAPEX' in u:
        return '$\%_{CAPEX}/year$'
        
    if 'C' in u:
        if 'CO2' in u:
            u = u.replace('CO2', 'CO_2')
        elif 'CHF' not in u:
            u = u.replace('C', r'C^\circ')

    
    return f'${u}$'

def latex_source(s):
    try:
        if 'None' in s or 'none' in s:
            return 'None'
        if 'Setting' in s or 'Default' in s or 'Tuned' in s:
            return s
        if 'and' in s:
            s = s.replace(' and ', ',')
            s = s.replace(' ','')
            
        s = s.replace(' ','_')
        
        return '\cite{' + s + '}'
    except:
        return s

df['Latex_symbol'] = df['Symbol'].apply(lambda x: f'${x}$')

df['Latex_value'] = df['Value'].apply(lambda x: latex_value(x))

df['Latex_unit'] = df['Units'].apply(lambda x: latex_units(x))

df['Latex_source'] = df['Source'].apply(lambda x: latex_source(x))
    
df = df.reindex(columns= ['Full name', 'Latex_symbol', 'Latex_value', 'Latex_unit', 'Latex_source', 
                          'Value', 'Units', 'Source', 'Description', 
                          'Symbol', 'Uncertainty'])

df.sort_values(['Category', 'Name'], inplace=True)
df.to_csv(os.path.join('inputs', 'latex_param.csv'))


df2['Latex_value'] = df2['Value'].apply(lambda x: latex_value(x))

df2['Latex_unit'] = df2['Units'].apply(lambda x: latex_units(x))

df2['Latex_source'] = df2['Source'].apply(lambda x: latex_source(x))

df2 = df2.reindex(columns= ['Latex_name', 'Latex_symbol', 'Latex_value', 'Latex_unit', 'Latex_source', 
                          'Value', 'Units', 'Source', 'Description', 
                          'Symbol', 'Uncertainty'])

df2.to_csv(os.path.join('inputs', 'latex_param_eco.csv'))



def sankey_drawings():
    """ Draw sanky diagrams for the figures """
    from matplotlib import pyplot as plt
    from matplotlib.sankey import Sankey
    
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(1, 1, 1, xticks=[], yticks=[],
                         title="Statistics from the 2nd edition of\nfrom Audio Signal Processing for Music Applications by Stanford University\nand Universitat Pompeu Fabra of Barcelona on Coursera (Jan. 2016)")
    learners = [14460, 9720, 7047, 3059, 2149, 351]
    labels = ["Total learners joined", "Learners that visited the course", "Learners that watched a lecture",
             "Learners that browsed the forums", "Learners that submitted an exercise", 
              "Learners that obtained a grade >70%\n(got a Statement of Accomplishment)"]
    colors = ["#FF0000", "#FF4000", "#FF8000", "#FFBF00", "#FFFF00"]
    
    sankey = Sankey(ax=ax, scale=0.0015, offset=0.3)
    for input_learner, output_learner, label, prior, color in zip(learners[:-1], learners[1:], 
                                                                  labels, [None, 0, 1, 2, 3],
                                                                 colors):
        if prior != 3:
            sankey.add(flows=[input_learner, -output_learner, output_learner - input_learner],
                   orientations=[0, 0, 1],
                   patchlabel=label,
                   labels=['', None, 'quit'],
                  prior=prior,
                  connect=(1, 0),
                   pathlengths=[0, 0, 2],
                  trunklength=10.,
                  rotation=0,
                      facecolor=color)
        else:
            sankey.add(flows=[input_learner, -output_learner, output_learner - input_learner],
                   orientations=[0, 0, 1],
                   patchlabel=label,
                   labels=['', labels[-1], 'quit'],
                  prior=prior,
                  connect=(1, 0),
                   pathlengths=[0, 0, 10],
                  trunklength=10.,
                  rotation=0,
                      facecolor=color)
    diagrams = sankey.finish()
    for diagram in diagrams:
        diagram.text.set_fontweight('bold')
        diagram.text.set_fontsize('10')
        for text in diagram.texts:
            text.set_fontsize('10')
    ylim = plt.ylim()
    plt.ylim(ylim[0]*1.05, ylim[1])
    

    
