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

# P = P.append(P_eco)
# P_meta = P_meta.append(P_eco_meta)

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
'Cost_per_size':    'Specific investement cost',
'Cost_per_unit':    'Fixed investement cost',
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
