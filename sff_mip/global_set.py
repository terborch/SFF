"""
### Declare global sets of units, resources and time periods
    #   Set of all units in the list Units
    #   Set of all resources in the list Resources
    #   Set of resource each unit produce and consume in dict Units_prod and Units_cons
    #   Set of units involved with each resource in dict U_res
    #   Set of time periods (index o to P) in list Periods
"""

# Units and resources
Units_full_name = ['Gas Boiler', 'Photovoltaic Panels', 'Battery', 'Solid Oxide Fuel cell', 
                   'Anaerobic Digester']
Units = ['BOI', 'PV', 'BAT', 'SOFC', 'AD']
Resources = ['Elec', 'Gas', 'Biogas', 'Biomass', 'Heat']

# The resources each unit produce
Units_prod = {
    'BOI':  ['Heat'],
    'PV':   ['Elec'],
    'BAT':  ['Elec'], 
    'SOFC': ['Elec', 'Heat'], 
    'AD':   ['Biogas']
    }

# The resources each unit consumes
Units_cons = {
    'BOI':  ['Gas'],
    'BAT':  ['Elec'], 
    'SOFC': ['Biogas'], 
    'AD':   ['Biomass', 'Elec', 'Heat']
    }

# The units producing and consuming a given resource
U_res = {
    'prod_Elec':['PV', 'BAT', 'SOFC'],
    'cons_Elec':['BAT', 'AD'],
    'prod_Heat':['BOI', 'SOFC'],
    'cons_Heat':['AD']
    }