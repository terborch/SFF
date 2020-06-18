import os
import results

# External modules
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Internal modules
import data
from global_set import Units
from data import get_param, time_param



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
# Time discretization
(Periods, Nbr_of_time_steps, dt, Day_dates, Time, dt_end, Days_all, Hours
 ) = time_param(S['Time'])

    
Time_steps = {'Days': Days_all, 'Hours': Hours, 'Periods': Periods}
# Default upper bound for most variables
Bound = S['Model','Var_bound']
# Dictionnary of variable metadata
V_meta = {}
V_meta['Header'] = ['Name', 'Value', 'Lower Bound', 'Upper Bound', 'Units', 'Decription', 'Type']
V_bounds = {}
# Dictionnary describing each constraint and its source if applicable
C_meta = {}


path = os.path.join('inputs', 'inputs.h5')
from results import get_hdf
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

AD_T = dic['AD_T'].values
Build_T = dic['build_T'].values



fig_width, fig_height = 11.7*2, 5.8
from matplotlib import pyplot as plt
def set_x_ticks(ax1, Time_steps):
    day_tics = [f'Day {d+1}' for d in Days]
    ax1.set_xticks(Time_steps[12::24], minor=False)
    ax1.set_xticklabels(day_tics, fontdict=None, minor=False)  


Time_steps = list(range(len(Hours)*len(Days)))

fig, ax1 = plt.subplots()
fig.set_size_inches(fig_width, fig_height)
plt.title('Building Electricity Consumption')
ax1.set_xlabel('Dates')
ax1.set_ylabel('Building Electricity Consumption in kW')
set_x_ticks(ax1, Time_steps)

n = 'Building Electricity Consumption'
ax1.plot(range(24), Build_cons['Elec'].flatten(), label=n)

plt.show()

fig, ax1 = plt.subplots()
fig.set_size_inches(fig_width, fig_height)
plt.title('Heat Consumption')
ax1.set_xlabel('Dates')
ax1.set_ylabel('Building Heat consumption in kW')
set_x_ticks(ax1, Time_steps)
ax2 = ax1.twinx()
ax2.set_ylabel('AD Heat Consumption in kW')
    
n = 'Building Heat Consumption'
ax1.plot(Time_steps, Build_cons['Heat'].flatten(), label=n, c='black')
n = 'AD Heat Consumption'
ax2.plot(Time_steps, AD_cons_Heat.flatten(), label=n, c='green')

plt.show()


Time_steps = list(range(len(Hours)*len(Days)))

fig, ax1 = plt.subplots()
fig.set_size_inches(fig_width, fig_height)
plt.title('Building Electricity Consumption')
ax1.set_xlabel('Dates')
ax1.set_ylabel('Building Electricity Consumption in kW')
set_x_ticks(ax1, Time_steps)

n = 'Building Electricity Consumption'
ax1.plot(range(24), Build_cons['Elec'].flatten(), label=n)

plt.show()