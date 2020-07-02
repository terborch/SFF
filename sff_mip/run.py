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
#import pandas as pd
import matplotlib.pyplot as plt
#import matplotlib
import numpy as np
from importlib import reload

start_construct = time.time()

# Internal modules
import model
import read_inputs
import results
#from param_input import V_meta, V_bounds, P, P_meta, Closest, Hours, Periods, Days
#from param_calc import Irradiance, Ext_T, Dates
import plot
#from plot import fig_width, fig_height


#Days = list(range(len(Closest)))

from read_inputs import Periods, Days, Hours

today = datetime.now().strftime("%Y-%m-%d")

end_construct = time.time()
print('model construct time: ', end_construct - start_construct, 's')


def run(objective, Reload=False, relax=False, Pareto=False, Limit=None,
        Plot=True, Summary=True, Save_txt=False):
    """ Solve the optimization model once then store the result in hdf5 format.
        # TODO save inputs into the resut folder
    """
    # Option to generate a new input.h5 file 
    if Reload:
        import write_inputs
        write_inputs.write_arrays('default', Cluster=False)
           
    
    start_solve = time.time()
    # Select objective and solve the model
    m = model.run(objective, relax=relax, Limit=Limit)
    
    end_solve = time.time()
    print('model solve time: ', end_solve - start_solve, 's')
    start_write = time.time()
    
    # Get results into python dictionnairies
    Threshold = 1e-6
    var_results, var_meta = results.get_all(m, Threshold, Days, Hours, Periods)  
    
    # Save all results to a hdf5 file
    file_name = 'results.h5'
    cd = results.make_path(objective=objective, Limit=Limit, Pareto=Pareto)
    path = os.path.join(cd, file_name)
    results.save_df_to_hdf5(var_results, var_meta, path, Days, Hours, Periods)
    
    # Save a txt file containing variable results close to the model limit
    if Save_txt:
        results.save_txt(m, cd)
        
    end_write = time.time()
    print('model write time: ', end_write - start_write, 's')
    
    # Plot graphs and save xls files of results
    start_plot = time.time()
    if Plot:
        plot.all_fig(path, save_fig=True)
    if Summary:
        results.summary(path, save=True)
    end_plot = time.time()
    
    # Save info about the run
    file_name = 'run_info.txt'
    info = {0: f'Objective:     {objective}',
            1: f'Limit:         {Limit}',
            2: f'Solve Time:    {end_solve - start_solve}',
            3: f'Write Time:    {end_write - start_write}',
            4: f'Plot Time:     {end_plot - start_plot}'}
    with open(os.path.join(cd, file_name), 'w') as f:
        for k in info.keys():
            print(info[k], file=f)

    return path
    
"""
def display_results(date=today, run_nbr='last', save_df=True, save_fig=True, 
                    big_vars=False, discard_fig=False):    
"""



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


def pareto(objective_cstr, objective_free, Plot=True, Summary=True):
    solve_time = []
    
    # Find the true minimum of objective_cstr
    path = run(objective_cstr, Pareto=True, Limit=None, Plot=Plot, Summary=Summary)
    min_obj_cstr = get_objective_value(objective_cstr, path)
    solve_time.append(time.time() - start)
    
    # Find the true maximum of objective_cstr
    path = run(objective_free, Pareto=True, Limit=None, Plot=Plot, Summary=Summary)
    max_obj_cstr = get_objective_value(objective_cstr, path)
    solve_time.append(time.time() - start)
    
    # Generate evenly distributed pareto points
    nsteps = 10 # Half of the number of pareto points
    epsilon = 1e-6
    step = (max_obj_cstr - min_obj_cstr)/(nsteps*2)
    Limits_lin = np.arange(min_obj_cstr, max_obj_cstr, step)
    Limits = np.concatenate((
        np.linspace(min_obj_cstr*(1 + epsilon), Limits_lin[6], num=nsteps), 
        np.linspace(Limits_lin[6], max_obj_cstr*(1 - epsilon), num=nsteps)[1:-1]))
    
    # print('\n')
    # print('min_obj_cstr', min_obj_cstr)
    # print('max_obj_cstr', max_obj_cstr)
    # print('Limits_lin', Limits_lin)
    # print('Limts', Limits)
    # print('\n')
    
    # Compute pareto points
    for i in range(1, len(Limits)):
        objective = 'limit_' + objective_cstr
        run(objective, Pareto=True, Limit=Limits[i], Plot=Plot, Summary=Summary)
        solve_time.append(time.time() - start)
        plt.close('all')
  
    # Plot pareto graphs
    plot.pareto(date=today)
    
    
def diagnostic(objective):
    """ Run the model with one of each heating system only """
    from global_set import U_res, Units
    import data
    
    # Set all units max capacity to zero
    for u in Units:
        data.change_settings(u, 'max_capacity', 0)  
    
    # For each heating unit solve for objective and store result
    for u in U_res['prod']['Heat']:
    # for u in ['EH']:
        data.change_settings(u, 'max_capacity', 1500) 
        reload(read_inputs)
        reload(model)
        run(objective)
        plt.close('all')
        data.change_settings(u, 'max_capacity', 0) 
    
    data.reset_settings()
    

if __name__ == "__main__":
    # Execute single run
    # run('emissions', Reload=True)
    # run('totex')
    #run_single('totex', save_fig=True, discard_fig=False)
    
    # Execute multi_run
    #pareto('capex', 'opex')
    pareto('emissions', 'totex', Plot=False, Summary=False)
    
    
    # diagnostic('totex')
    
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






# Attempt at a smoothly distributed pareto graph

# pareto = {}
# def y(x):
#     return 860.9098 + 38512.62*(np.e)**(-10.05036*x)
# x = np.arange(0.3,1.3,0.1)
# x_max, x_min = max(x), min(x)
# y_max, y_min = max(y(x)), min(y(x))
# Dx = x_max - x_min
# Dy = y_max - y_min
# def mid_point(x1, x2, y1, y2):
#     dx = np.abs((x1 - x2))/Dx
#     dy = np.abs((y1 - y2))/Dy
#     if dx > dy:
#         return np.abs(x1 - x2)/2
#     else:
#         return np.abs(y1 - y2)/2
#     pass
    
# pareto[0] = [x_min, y(x_min)]
# pareto[10] = [x_max, y(x_max)]
# pareto[5] = [(x_max + x_min)/2, y((x_max + x_min)/2)]


# plt.plot(x,y(x))
# for p in pareto:        
#     plt.scatter(pareto[p][0], pareto[p][1], color='black')    
# plt.show()