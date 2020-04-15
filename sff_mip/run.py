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
from initialize_model import m, S, V_meta
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

var_result_time_indep, var_result_time_dep = results.all_dic(m, Periods)
var_name_time_indep, var_name_time_dep = var_result_time_indep.keys(), var_result_time_dep.keys()



time_dep_summary_dic = {}
for v in var_result_time_dep:
    value = var_result_time_dep[v]
    time_dep_summary_dic[v] = [min(value), np.mean(value), max(value), len(value)]

df_results = results.var_time_indep_summary(m, var_result_time_indep, V_meta)

pd.options.display.max_rows = 50
pd.options.display.max_columns = 10
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
    
ax2.plot(date[:-1], var_result_time_dep['build_T'], color='black', label='Building Temperature')
ax2.plot(date[:-1], var_result_time_dep['unit_T[AD]'], color='green', label='AD Temperature')
plt.legend()

plt.show()

print('gas import in kwh: ', m.getVarByName('grid_import_a[Gas]').x)

end = time.time()

print('solve time all: ', end - start, 's')

def sorted_index(unsorted_list):
    """ Given a list of lists returns an index (lost of pairs) where the first element is 0, 1, 2... n 
        the new index sorted by the largest element in each list in decreasing order. The second element
        is the index of the same list in the original list of list.
    """
    new_index = []
    j = 0
    for i in range(0,len(unsorted_list)):
        new_index.append([max(unsorted_list[i]), j])
        j += 1
        
    new_index.sort(reverse = True)
    
    for i in range(0, len(new_index)):
        new_index[i][0] = i
        
    return new_index 


def sort_from_index(unsorted_list, new_index):
    sorted_list = [ [] for i in range(len(new_index)) ]
    for i in new_index:
        sorted_list[i[0]] = unsorted_list[i[1]]
        
    return sorted_list


def plot_flows(indicator, name, units, sort = False):
    plt.title(name)
    plt.xlabel('Date')
    plt.ylabel(name + units)
    # Get relevant flows according to indicator
    flows, flows_name = [], []
    for n in var_result_time_dep:
        if indicator in n:
            flows.append(var_result_time_dep[n]+ [0])
            flows_name.append(n)
    # Sort in decreasing order each flow by maximum value
    if sort:
        flows_sort = sort_from_index(flows, sorted_index(flows))
        flows_name_sort = sort_from_index(flows_name, sorted_index(flows))
    else: flows_sort, flows_name_sort = flows,  flows_name
    
    # Transpose the list of flows
    flows_T_sort = list(map(list, zip(*flows_sort)))
    plt.plot(date, flows_T_sort)
    plt.legend(flows_name_sort)
    
    
###plot_flows('v[', 'water flows', 'm^3/h')
###plot_flows('Heat', 'heat flows', 'kW') 
plot_flows('[BAT][', 'Battery', 'kW') 
plot_flows('[PV][', 'AD production', 'kW')
plt.show()
##################################################################################################
### END
##################################################################################################
