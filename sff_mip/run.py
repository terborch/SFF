""" Main script from where to run all other scripts
    #   TODO: Set file names and path  
    #   Get all imputs
    #   TODO: options to view and save imputs
    #   Build the MIP model
    #   TODO: add option to change scenarios
    #   TODO: add option to change model settings and parameters
    #   TODO: option to view and save the model
    #   Get and display outputs
    #   Option to save outputs
    #   TODO: Save format, save graphs
 
"""


# External modules
import os.path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import time
import numpy as np

start = time.time()


# Internal modules
import results
from initialize_model import m, S
from global_param import Costs_u, Periods, Ext_T, Irradiance
import model
import data

# Build and run the MIP optimization model
relax = False
model.run(relax)


end = time.time()
print('solve time model: ', end - start, 's')

# datetime object containing current date and time
now = datetime.now()
now = now.strftime("%Y-%m-%d")

vars_name, vars_value, vars_unit, vars_lb, vars_ub = [], [], [], [], []
    
df_results = results.time_indep(m, Costs_u)

time_indep_var, time_dep_var = results.var_names(m)


time_indep_dic, time_dep_dic = results.get_all_var(m, time_dep_var, Periods)
time_dep_summary_dic = {}
for v in time_dep_dic:
    value = time_dep_dic[v]
    time_dep_summary_dic[v] = [min(value), np.mean(value), max(value), len(value)]

pd.set_option('precision', 2)
c = ['Minimum', 'Average', 'Maximum', 'Length']
df = pd.DataFrame(time_dep_summary_dic).T
df.columns = c
print(df)

run_nbr = 1

cd = os.path.join('results', 'run_{}_on_{}'.format(run_nbr, now), 'result_summary')

print(df_results)

save = False
if save:
    os.makedirs(os.path.dirname(cd), exist_ok=True)
    
    df_results.to_csv(cd + '.csv')
    
    df_results.to_pickle(cd + '.pkl')
    
    df = pd.read_pickle(cd + '.pkl')
    
    with open('vars_above_10k.txt', 'w') as f:
        for v in m.getVars():
            if v.x > 10000:
                print(v.varName + ': {:.2f}\n'.format(v.x), file=f)
                
    with open('vars_all.txt', 'w') as f:
        for v in m.getVars():
                print(v.varName + ': {:.2f}\n'.format(v.x), file=f)

##################################################################################################
### Messy result plot
##################################################################################################


plt.rcParams['figure.figsize'] = [15, 5]
period_start = S['Period_start'] + ' ' + S['Period_start_time']
period_end = S['Period_end'] + ' ' + S['Period_start_time']
timestep = S['Time_step']
file = 'meteo_Liebensberg_10min.csv'

df_weather = data.weather_data_to_df(file, period_start, period_end, timestep)

date = df_weather.index
irr = df_weather['Irradiance']
temp = df_weather['Temperature']

fig, ax1 = plt.subplots()

c = 'red'
ax1.set_xlabel('Date')
ax1.set_ylabel('Irradiance in kW')
ax1.plot(date, irr, color=c, label='Irradiance')
ax1.tick_params(axis='y', labelcolor=c)
fig.autofmt_xdate()

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

c = 'blue'
ax2.set_ylabel('Temperature in °C')  # we already handled the x-label with ax1
ax2.plot(date, temp, color=c, label='Exterior Temperature')
ax2.tick_params(axis='y', labelcolor=c)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.title('Weather data for Liebensberg from ' + S['Period_start']  + ' to ' + S['Period_end'] + 
          'and building temperatures')
    
ax2.plot(date[:-1], time_dep_dic['build_T'], color='black', label='Building Temperature')
ax2.plot(date[:-1], time_dep_dic['unit_T[AD]'], color='green', label='AD Temperature')
plt.legend()

plt.show()

print('gas import in kwh: ', m.getVarByName('grid_gas_import').x)

end = time.time()

print('solve time all: ', end - start, 's')


plt.title('water volume flows')
plt.xlabel('Date')
plt.ylabel('Volume flow')
volume_flows = []
for n in time_dep_dic:
    if 'v[' in n:
        volume_flows.append(time_dep_dic[n]+ [0])
plt.plot(date, np.array(volume_flows).T)
plt.legend()
plt.show()
##################################################################################################
### END
##################################################################################################
