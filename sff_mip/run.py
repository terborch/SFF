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
    #   TODO: Fix the broken Pareto
 
"""
import time
start = time.time()

# External modules
import os.path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

start_construct = time.time()

# Internal modules
import results
from param_input import V_meta, V_bounds, P, P_meta, Closest, Hours, Periods, Days
from param_calc import Irradiance, Ext_T, Dates
import model
import plot
from plot import fig_width, fig_height

Days = list(range(len(Closest)))

today = datetime.now().strftime("%Y-%m-%d")

end_construct = time.time()
print('model construct time: ', end_construct - start_construct, 's')


def run(objective, Reload=True, relax=False, Pareto=False, Limit=None, Save_txt=False):
    """ Solve the optimization model once then store the result in hdf5 format.
        # TODO save inputs into the resut folder
    """
    
    # Option to generate a new input.h5 file 
    if Reload:
        pass
           
    
    start_solve = time.time()
    # Select objective and solve the model
    m = model.run(objective, relax=relax, Limit=Limit)
    
    end_solve = time.time()
    print('model solve time: ', end_solve - start_solve, 's')
    start_write = time.time()
    
    # Get results into python dictionnairies
    Threshold = 1e-9
    var_results, var_meta = results.get_all(m, Threshold, Days, Hours, Periods)  
    
    # Save all results to a hdf5 file
    file_name = 'results.h5'
    cd = results.make_path(objective=objective, Limit=Limit, Pareto=Pareto)
    path = os.path.join(cd, file_name)
    results.save_df_to_hdf5(var_results, var_meta, path, Days, Hours, Periods)
    
    if Save_txt:
        results.save_txt(m, cd)
        
    end_write = time.time()
    print('model write time: ', end_write - start_write, 's')
    
    plot.all_fig(path, save_fig=True)
    results.summary(path, save=True)

    if Pareto:
        return path
    
"""
def display_results(date=today, run_nbr='last', save_df=True, save_fig=True, 
                    big_vars=False, discard_fig=False):    
"""

# Execute single run
#run('emissions')

#run_single('totex', save_fig=True, discard_fig=False)


# # Dicts of all variables and their results
# var_result_time_indep, var_result_time_dep = results.all_dic(m, Periods, V_bounds)
# var_name_time_indep = list(var_result_time_indep.keys())
# var_name_time_dep = list(var_result_time_dep.keys())


Results = {}

Objective_description = {
    'totex': 'TOTEX minimization', 
    'emissions': 'Emissions minimization',
    'pareto_totex':'Emissions minimization with constrained TOTEX at the minimum',
    'pareto_emissions': 'TOTEX minimization with constrained emissions at the minimum',
    }

def get_objective_value(objective, path):
    df = results.get_hdf(path, 'single')
    df.set_index('Var_name', drop=True, inplace=True)
    return df['Value'][objective]


def pareto(objective_cstr, objective_free):
    solve_time = []
    
    path = run(objective_cstr, Pareto=True, Limit=None)
    min_obj_cstr = get_objective_value(objective_cstr, path)
    solve_time.append(time.time() - start)
    
    path = run(objective_free, Pareto=True, Limit=None)
    max_obj_cstr = get_objective_value(objective_cstr, path)
    solve_time.append(time.time() - start)
    
    # Half of the number of steps
    nsteps = 5
    epsilon = 1e-6
    step = (max_obj_cstr - min_obj_cstr)/(nsteps*2)
    Limits = np.arange(min_obj_cstr, max_obj_cstr, step)
    
    # Limits= np.concatenate((
    #     np.linspace(min_obj_cstr*(1 + epsilon), Limits_lin[2], num=nsteps), 
    #     np.linspace(Limits_lin[2], max_obj_cstr*(1 - epsilon), num=nsteps)[1:]))
    
    # print('\n')
    # print('min_obj_cstr', min_obj_cstr)
    # print('max_obj_cstr', max_obj_cstr)
    # print('Limits_lin', Limits_lin)
    # print('Limts', Limits)
    # print('\n')
    
    for i in range(1, len(Limits)):
        objective = 'limit_' + objective_cstr
        run(objective, Pareto=True, Limit=Limits[i])
        solve_time.append(time.time() - start)
        plt.close('all')
  
#pareto('capex', 'opex')
pareto('emissions', 'totex')

#solve_time.append([time.time() - solve_time[i]])
end = time.time()

print('global runtime: ', end - start, 's')
# for i in range(10):
#     print(f'Pareto_{i}_solve_time', solve_time[i] )

"""
path = run('opex', Pareto=True, Limit=None)
df = results.get_hdf(path, 'single')
df.set_index('Var_name', drop=True, inplace=True)
df['Value']['capex']
"""

"""
date=today
run_nbr='last'
    
cd = os.path.join('results', '{}'.format(date))
    
if run_nbr == 'last':
    run_nbr = results.get_last_run_nbr(cd)

file_name = 'results.h5'
path = os.path.join(cd, f'run_nbr_{run_nbr}', file_name)


import plot
plot.all_fig(path, save_fig=True)
"""

       
##################################################################################################
### END
##################################################################################################

















##################################################################################################
### Display
##################################################################################################





"""


    
    
    # Dicts of all variables and their results
    var_results, var_bounds = results.get_all(m, Days, Hours, Periods)
    var_names = {'time_indep': None, 'time_dep': None}
    for t in ['time_indep', 'time_dep']:
        var_names[t] = list(var_results[t].keys())
        var_names[t].sort()
    
    var_result_time_indep, var_result_time_dep = var_results['time_indep'], var_results['time_dep']
    var_name_time_indep = list(var_result_time_indep.keys())
    var_name_time_dep = list(var_result_time_dep.keys())
        
    df_time_indep = results.var_time_indep_summary(m, var_result_time_indep, V_meta)
    df_time_dep = results.var_time_dep_summary(m, var_result_time_dep, V_meta, var_bounds['time_dep'])
    df_parameters = results.parameters(P, P_meta)
    
    # display result summary
    pd.options.display.max_rows = 50
    pd.options.display.max_columns = 10
    pd.set_option('precision', 2)

    if not Pareto:
        print(df_time_indep)
        print(df_time_dep)
    
    matplotlib.rcParams['figure.figsize'] = (fig_width, fig_height)
    plot.unit_results(var_result_time_indep, var_name_time_indep)
    plt.show()
    

        

        
"""