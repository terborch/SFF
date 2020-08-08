import os

import numpy as np

# Internal modules
from data import (get_param, time_param, get_hdf, open_csv, to_date_time, 
                  reshape_day_hour)



###############################################################################
### Function used in both write and read
###############################################################################

path = os.path.join('inputs', 'precalc.h5')

P, _ = get_param('parameters.csv')
P_calc, _ = get_param('calc_param.csv')
P_eco, _ = get_param('cost_param.csv')
P = P.append(P_calc)
P = P.append(P_eco)
# Dictionnaries of values and metadata from the file 'Settings.csv'
S, _ = get_param('settings.csv')
# S, _ = get_param('settings_no_WBOI.csv')
# S, _ = get_param('settings_SFF_current.csv')
# Time discretization
(Periods, Nbr_of_time_steps, dt, Day_dates, Time, dt_end, Days_all, Hours
 ) = time_param(S['Time'])

    
Time_steps = {'Days': Days_all, 'Hours': Hours, 'Periods': Periods}
# Default upper bound for most variables
Bound = S['Model','Var_bound']
Tight = S['Model','Var_bound_tight']
# Dictionnary of variable metadata
V_meta = {}
V_meta['Header'] = ['Name', 'Value', 'Lower Bound', 'Upper Bound', 'Units', 
                    'Decription', 'Type']
V_bounds = {}
# Dictionnary describing each constraint and its source if applicable
C_meta = {}

path = os.path.join('inputs', 'inputs_palezieux.h5')
# path = os.path.join('inputs', 'inputs.h5')
# path = os.path.join('inputs', 'no_clusters.h5')
dic = get_hdf(path)


Build_cons = {}
Build_cons['Elec'] = dic['Build_cons_Elec'].values
Build_cons['Heat'] = dic['build_Q'].values
Time_period_map = dic['Time_period_map'].values
Days = list(range(len(dic['Days'])))
Ext_T = dic['Ext_T'].values
AD_cons_Heat = dic['AD_Q'].values
Frequence = dic['Frequence'].values
Irradiance = dic['Irradiance'].values
Elec_CO2 = dic['Elec_CO2'].values
Fueling = dic['Fueling_profile'].values

AD_T = dic['AD_T'].values
Build_T = dic['build_T'].values

# Corrections concerning Tractors and fueling based on inputs
P['GFS', 'Cost_per_unit'] = P['GFS', 'Total_cost']*0.3
P['GFS', 'Cost_per_size'] = P['GFS', 'Total_cost']*0.7/np.max(Fueling)
P['GFS', 'Cost_per_unit'] += P['GFS', 'Conversion_cost']*P['Farm', 'nbr_tractors']

# Whether or not Wood is considered a reneable resource
if S['WBOI', 'Is_renewable']:
    pass
else:
    P['Wood', 'Emissions'] = P['Gas', 'Emissions']
