"""
### Declare global sets of units and resources - They are immutable (tuples) or treated as such
    #   Abbrev      dict of abbreviations
    #   Units       tuple of all units in the list units
    #   Resources   tuple of resources
    #   U_prod      dict of resource each unit produce
    #   U_cons      dict of resource each unit consume 
    #   U_res       dict of units producing and consuming each resource
    #   U_storage   tuple of storage units
    #   Heat_cons   tuple of units and buildings consuming heat
    #   Heat_prod   tuple of units producing heat
    #   G_res       tuple of resources exchanged by the grid
    #   Color_code      dict of colors, one for each resource
    #   Linestyle_code  dict of linestyle names, on for each unit building and grid
    #   Linestyles      dict relating linestyle names to linestyles
"""

# Abbreviations
Abbrev = {'GBOI':   'Gas Boiler',
          'WBOI':   'Wood Boiler', 
          'EH':     'Electric Heater',
          'AHP':    'Air-Air Heat Pump',
          'GHP':    'Geothermal Heat Pump',
          'PV':     'Photovoltaic Panels', 
          'BAT':    'Battery',
          'GCSOFC': 'Gas Cleaning for SOFC',
          'SOFC':   'Solid Oxide Fuel cell',
          'ICE':    'Internal Combustion Engine',
          'AD':     'Anaerobic Digester',
          'CGT':    'Compressed Gas Tank',
          'BS':     'Biogas Storage',
          'BU':     'Biogas Upgrading',
          'GFS':    'Gas Fueling Station',
          'build':  'building',
          'Elec':   'Electricity',
          'Gas':    'Natural Gas or Syntetic NG',
          'Biogas': '60% CH4, 40% CO2',
          'Heat':   'Heat',
          'BM':     'Bio-methane'
          }

# Eneregy conversion units
Units = ('GBOI', 'WBOI', 'EH', 'AHP', 'GHP',    # Heating
         'ICE', 'SOFC',                         # Cogeneration
         'PV', 'AD',                            # Energy Production
         'BAT', 'CGT', 'BS',                    # Energy Storage
         'GCSOFC', 'GFS', 'BU')                 # Utility

# Resources and energy carriers
Resources = ('Elec', 'Gas', 'Wood', 'Biogas', 'BM', 'Biomass', 'Heat', 'Diesel')

# The resources each unit produce
U_prod = {
    'GBOI':     ('Heat',),
    'WBOI':     ('Heat',),
    'EH':       ('Heat',),
    'AHP':      ('Heat',),
    'GHP':      ('Heat',),
    'PV':       ('Elec',),
    'BAT':      ('Elec',),
    'GCSOFC':   ('Biogas', 'BM'),
    'SOFC':     ('Elec', 'Heat'),
    'ICE':      ('Elec', 'Heat'),
    'AD':       ('Biogas',),
    'CGT':      ('BM',),
    'BS':       ('Biogas',),
    'BU':       ('BM',),
    'GFS':      ('BM', 'Gas')
    }

# The resources each unit consumes
U_cons = {
    'GBOI':     ('Gas', 'Biogas', 'BM'),
    'WBOI':     ('Wood',),
    'EH':       ('Elec',),
    'AHP':      ('Elec',),
    'GHP':      ('Elec',),
    'BAT':      ('Elec',),
    'GCSOFC':   ('Elec', 'Biogas', 'BM'),
    'SOFC':     ('Gas', 'Biogas', 'BM'),
    'ICE':      ('Gas', 'Biogas', 'BM'),
    'AD':       ('Biomass', 'Elec', 'Heat'),
    'CGT':      ('BM', 'Elec'),
    'BS':       ('Biogas', 'Elec'),
    'BU':       ('Biogas', 'Elec'),
    'GFS':      ('BM', 'Gas', 'Elec')
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
Units_storage = ('BAT', 'CGT', 'BS')

# The buildings and units consuming and producing heat
Heat_cons = tuple(['build'] + list(U_res['cons']['Heat']))
Heat_prod = U_res['prod']['Heat']

# Resources that can be exchanged with the grids
G_res = ('Elec', 'Gas', 'Wood', 'Diesel', 'BM')

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
                  'ICE':    'dashed',
                  'GCSOFC': 'solid',
                  'BU':     'solid',
                  'AD':     'dashdotted', 
                  'build':  'densely dashdotted', 
                  'GBOI':   'loosely dashed',
                  'WBOI':   'loosely dashed',
                  'EH':     'loosely dashed',
                  'AHP':    'loosely dashed',
                  'GHP':    'loosely dashed',
                  'CGT':    'densely dashdotdotted',
                  'BS':     'densely dashdotdotted',
                  'GFS':    'solid',
                  'default':'solid'
                  }

# Colors for differentiating resources
Color_code = {'Elec':       'royalblue', 
              'Biogas':     'limegreen',
              'BM':         'green',
              'Biomass':    'khaki', 
              'Gas':        'gray',
              'Wood':       'brown',
              'Heat':       'firebrick', 
              'Ext_T':      'navy', 
              'Irradiance': 'red', 
              'Diesel':     'black',
              'default':    'purple'
              }

