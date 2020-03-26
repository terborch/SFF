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
from initialize_model import m
from global_param import U_c, Periods, Temperature, Irradiance
import model


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

cd = os.path.join('results', 'run_{}_on_{}'.format(run_nbr, now), 'result_summary.pkl')

os.makedirs(os.path.dirname(cd), exist_ok=True)

df_results.to_pickle(cd)

df = pd.read_pickle(cd)

print(df_results)

time_indep_dic, time_dep_dic = results.get_all_var(m, vars_name_t, Periods)

plt.plot(Periods, Temperature)
plt.plot(Periods, time_dep_dic['building_temperature'])
plt.show()

##################################################################################################
### END
##################################################################################################
