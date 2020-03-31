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
# Internal modules
import results
from initialize_model import m, S
from global_param import U_c, Periods, Temperature, Irradiance
import model
import data

# Build and run the MIP optimization model
relax = False
model.run(relax)


# datetime object containing current date and time
now = datetime.now()
now = now.strftime("%Y-%m-%d")

vars_name, vars_value, vars_unit, vars_lb, vars_ub = [], [], [], [], []
    
df_results = results.time_indep(m, U_c)

vars_name_t = results.time_dep_var_names(m)

run_nbr = 1

cd = os.path.join('results', 'run_{}_on_{}'.format(run_nbr, now), 'result_summary')

os.makedirs(os.path.dirname(cd), exist_ok=True)

df_results.to_csv(cd + '.csv')

df_results.to_pickle(cd + '.pkl')

df = pd.read_pickle(cd + '.pkl')

print(df_results)





##################################################################################################
### Messy result plot
##################################################################################################


plt.rcParams['figure.figsize'] = [15, 5]
period_start = S['Period_start'] + ' ' + S['Period_start_time']
period_end = S['Period_end'] + ' ' + S['Period_start_time']
timestep = S['Time_step']
file = 'meteo_Liebensberg_10min.csv'

df_weather = data.weather_data_to_df(file, period_start, period_end, timestep)

time = df_weather.index
irr = df_weather['Irradiance']
temp = df_weather['Temperature']

fig, ax1 = plt.subplots()

c = 'red'
ax1.set_xlabel('Date')
ax1.set_ylabel('Irradiance in kW')
ax1.plot(time, irr, color=c, label='Irradiance')
ax1.tick_params(axis='y', labelcolor=c)
fig.autofmt_xdate()

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

c = 'blue'
ax2.set_ylabel('Temperature in °C')  # we already handled the x-label with ax1
ax2.plot(time, temp, color=c, label='External Temperature')
ax2.tick_params(axis='y', labelcolor=c)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.title('Weather data for Liebensberg from ' + S['Period_start']  + ' to ' + S['Period_end'])
    
time_indep_dic, time_dep_dic = results.get_all_var(m, vars_name_t, Periods)
ax2.plot(time[:-1], time_dep_dic['building_temperature'], color='green', label='Internal Temperature')
plt.legend()

plt.show()

print('gas import in kwh: ', m.getVarByName('grid_gas_import').x)


##################################################################################################
### END
##################################################################################################
