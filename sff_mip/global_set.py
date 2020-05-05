"""
### Declare global sets of units and resources
    #   Abbrev      dict of abbreviations
    #   Units       list of all units in the list units
    #   Resources   list of resources
    #   U_prod      dict of resource each unit produce
    #   U_cons      dict of resource each unit consume 
    #   U_res       dict of units producing and consuming each resource
    #   U_storage   list of storage units
    #   Heat_cons   list of units and buildings consuming heat
    #   Heat_prod   list of units producing heat
    #   G_res       list of resources exchanged by the grid
    #   Color_code      dict of colors, one for each resource
    #   Linestyle_code  dict of linestyle names, on for each unit building and grid
    #   Linestyles      dict relating linestyle names to linestyles
"""

# Abbreviations
Abbrev = {'BOI':    'Gas Boiler', 
          'PV':     'Photovoltaic Panels', 
          'BAT':    'Battery', 
          'SOFC':   'Solid Oxide Fuel cell', 
          'AD':     'Anaerobic Digester',
          'CGT':    'Compressed Gas Tank',
          'build':  'building',
          'Elec':   'Electricity',
          'Gas':    '(Synthetic) Natural Gas',
          'Biogas': '60% CH4, 40% CO2',
          'Heat':   'Heat'
          }

# Eneregy conversion units
Units = ('BOI', 'PV', 'BAT', 'SOFC', 'AD', 'CGT')

# Resources and energy carriers
Resources = ('Elec', 'Gas', 'Biogas', 'Biomass', 'Heat')

# The resources each unit produce
U_prod = {
    'BOI':  ('Heat',),
    'PV':   ('Elec',),
    'BAT':  ('Elec',), 
    'SOFC': ('Elec', 'Heat'), 
    'AD':   ('Biogas',),
    'CGT':  ('Biogas',) 
    }

# The resources each unit consumes
U_cons = {
    'BOI':  ('Gas', 'Biogas'),
    'BAT':  ('Elec',), 
    'SOFC': ('Gas', 'Biogas'), 
    'AD':   ('Biomass', 'Elec', 'Heat'),
    'CGT':  ('Biogas', 'Elec')
    }

# The units producing and consuming a given resource
# Dictionnary format: U_res['prod']['Elec'] = ['PV', 'BAT', 'SOFC']
U_res = {'prod': {}, 'cons': {}}
for r in Resources:
    for u in U_prod:
        U_res['prod'][r] = tuple(u for u in U_prod if r in U_prod[u])
    for u in U_cons:
        U_res['cons'][r] = tuple(u for u in U_cons if r in U_cons[u])

# Units that store energy
Units_storage = ['BAT', 'CGT']

# The buildings and units consuming and producing heat
Heat_cons = tuple(['build'] + list(U_res['cons']['Heat']))
Heat_prod = U_res['prod']['Heat']

# Resources that can be exchanged with the grids
G_res = ('Elec', 'Gas')

# Linestyles for differentiating units
Linestyles = {'loosely dotted': (0, (1, 10)),
              'loosely dashed': (0, (5, 10)),
              'dashdotted': (0, (3, 5, 1, 5)),
              'densely dashdotted': (0, (3, 1, 1, 1)),
              'densely dashdotdotted': (0, (3, 1, 1, 1, 1, 1))
              }

Linestyle_code = {'PV':     'dotted', 
                  'BAT':    'dashdot', 
                  'grid':   'solid', 
                  'SOFC':   'dashed', 
                  'AD':     'dashdotted', 
                  'build':  'densely dashdotted', 
                  'BOI':    'loosely dashed',
                  'CGT':    'densely dashdotdotted',
                  'default':'solid'
                  }

# Colors for differentiating resources
Color_code = {'Elec':       'royalblue', 
              'Biogas':     'limegreen', 
              'Biomass':    'khaki', 
              'Gas':        'gray', 
              'Heat':       'firebrick', 
              'Ext_T':      'navy', 
              'Irradiance': 'red', 
              'Diesel':     'black',
              'default':    'purple'
              }
