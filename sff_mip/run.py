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
import matplotlib.pyplot as plt
import numpy as np
from importlib import reload
from data import get_param

start_construct = time.time()

# Internal modules
import model
import read_inputs
import results
import plot

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
        write_inputs.write_arrays('default', Cluster=True)
           
    
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
            # for v in m.getVars():
            #     if v.x > 2000:
            #         print('Warning high variable value', file=f)
            #         print('{}: {:.0f}'.format(v.VarName, v.x), file=f)
    return path
    
"""
def display_results(date=today, run_nbr='last', save_df=True, save_fig=True, 
                    big_vars=False, discard_fig=False):    
"""



Results = {}

Objective_description = {
    'totex': 'TOTEX minimization', 
    'envex': 'Emissions minimization',
    'pareto_totex': 'Emissions minimization with constrained TOTEX at the minimum',
    'pareto_envex': 'TOTEX minimization with constrained emissions at the minimum',
    }


def get_objective_value(objective, path):
    df = results.get_hdf(path, 'single')
    df.set_index('Var_name', drop=True, inplace=True)
    return df['Value'][objective]


def pareto(objective_x, objective_y, N_points, Plot=True, Summary=True):
    
    
    def disctance(x, y):
        """ Given x, y coordinates of n points returns the euclidean distance
            between each set of two points that follows each other.
        """
        N_points = len(x)
        d = []
        for i in range(N_points - 1):
            d.append(((x[i] - x[i+1])**2 + (y[i] - y[i+1])**2)**0.5)
        return d
    
    def choose_objective(x1, x2, y1, y2):
        """ Calculates the slope between two points and terun 'x' if it is lower
            than 1 and 'y' if it is greater than 1. (absolute value)
        """
        m = (y2 - y1)/(x2 - x1)
        if np.abs(m) <= 1:
            return objective_x
        else:
            return objective_y
    
    def make_point(s, obj, x, y):
        """ Make a new point in the middle of a segment s, relative to an objective
            and insert it to the x, y list of points.
        """
        objective = 'limit_' + obj
        
        if obj == objective_x:
            limit = (x[s] - x[s-1])/2 + x[s-1]
        elif obj == objective_y:
            limit = (y[s-1] - y[s])/2 + y[s]
   
        path = run(objective, Pareto=True, Limit=limit, Plot=Plot, Summary=Summary)
        solve_time.append(time.time() - start)
        plt.close('all')
        x.insert(s, get_objective_value(objective_x, path))
        y.insert(s, get_objective_value(objective_y, path))
    
        
    solve_time = []
    # Find the true minimum of objective_x
    path = run(objective_x, Pareto=True, Limit=None, Plot=Plot, Summary=Summary)
    min_x = get_objective_value(objective_x, path)
    max_y = get_objective_value(objective_y, path)
    solve_time.append(time.time() - start)
    
    # Find the true maximum of objective_y
    path = run(objective_y, Pareto=True, Limit=None, Plot=Plot, Summary=Summary)
    max_x = get_objective_value(objective_x, path)
    min_y = get_objective_value(objective_y, path)
    solve_time.append(time.time() - start)
    
    # Relaxation 1%
    r = 0.01

    # Find the true minimum of objective_x
    path = run('limit_' + objective_y, Pareto=True, Limit=min_y*(1 + r), Plot=Plot, Summary=Summary)
    min_y = get_objective_value(objective_y, path)
    max_x = get_objective_value(objective_x, path)
    solve_time.append(time.time() - start)
    

    # Find the true maximum of objective_y
    path = run('limit_' + objective_x, Pareto=True, Limit=min_x*(1 + r), Plot=Plot, Summary=Summary)
    min_x = get_objective_value(objective_x, path)
    max_y = get_objective_value(objective_y, path)
    solve_time.append(time.time() - start)
    N_points = N_points + 1
        
    # List of pareto results
    x = [min_x, max_x]
    y = [max_y, min_y]
    
    # add n new pareto points to the x, y list
    for i in range(N_points - 3):
        # Longest segment number
        s = np.argmax(disctance(x, y)) + 1
        # Objective according to slope
        obj = choose_objective(x[s], x[s-1], y[s], y[s-1])
        # Insert new point in the middle of the longest segment
        make_point(s, obj, x, y)
    
    
    # Plot pareto graphs
    plot.pareto(date=today, Xaxis=objective_x, Yaxis=objective_y)
    
    # plt.scatter(x,y)
    
    
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


def slim_run(objective, querry, *file_path,
             Limit=None, New_Pamar=None, New_Setting=None):
    """ Minimalistic run function, solve the model with given inputs
        and returns a name-value dictionnary for each item in the querry list
        Saves all results in a hdf5 file to the specified path.
    """
    # Solve the model
    m = model.run(objective, Limit=Limit, 
                  New_Pamar=New_Pamar, New_Setting=New_Setting)
        
    # Querry variable values
    Querried_results = {}
    for q in querry:
        Querried_results[q] = m.getVarByName(q).x

    if file_path:         
        # Save results to path
        var_results, var_meta = results.get_all(m, 1e-6, 
                                                Days, Hours, Periods)    
        results.save_df_to_hdf5(var_results, var_meta, file_path[0], 
                                Days, Hours, Periods)
    
    return Querried_results


def make_folder(param_index, variation, folder_path):
    """ Create a new folder inside folder_path based on the Param_index
        and variation. Return a path to the new folder. """
    
    param_name = '_'.join(param_index)
    new_folder = '_'.join([param_name, '{:.2g}'.format(variation)])

    os.makedirs(os.path.dirname(os.path.join(folder_path, new_folder, '')), 
                exist_ok=True)
    
    return os.path.join(folder_path, new_folder)
    
def get_default_param():
    P, P_meta = get_param('parameters.csv')
    P_calc, P_meta_calc = get_param('calc_param.csv')
    P_eco, P_meta_eco = get_param('cost_param.csv')
    P, P_meta = P.append(P_calc), P_meta.append(P_meta_calc)
    P, P_meta = P.append(P_eco), P_meta.append(P_meta_eco)
    return P, P_meta
    
def sensitsivity_analysis():
    """ Performs a sensitivity analysis on the selected parameters using the 
        One At a Time approach.
    """
    folder_path = os.path.join('results', 'sensitivity_analysis')
    list_of_files = [f for f in os.listdir(folder_path)]
    
    # 1. Select what parameter to modify and use this new value as input.
    P, P_meta = get_default_param()
    start = time.time()
    variation = P_meta['Uncertainty']
    totex_min_SFF, envex_min = {}, {}
    pt_5_dict, pt_15_dict = {}, {}
    for i in variation[variation > 0].index:
        print(i, '{:.2g}'.format(P[i]*(1 + variation[i])), '{:.2g}'.format(P[i]), 
              '{:.2g}'.format(P[i]*(1-variation[i])))
        
        # Reset all input parameters to default values
        P, _ = get_default_param()
        for p in [1, -1]:
            # Param index i, Positivie or Negative p, Variation variation[i]
            P[i] = P[i]*(1 + p*variation[i])
            
            path = make_folder(i, 1 + p*variation[i], folder_path)
            path_separator = os.path.join('a', 'a').split('a')[1]
            if path.split(path_separator)[-1] in list_of_files:
                continue
            # 2. Run the optimizer with a new parameter value
             # 2.1 Pinpoint and solve pareto point 5 on the envex-totex graph
              # 2.1.1 Get the TOTEX min for the current SFF scenario
            file_path = os.path.join(path, 'current_SFF.h5')
            S, _ = get_param('settings_SFF_current.csv')
            totex_min_SFF[i] = slim_run('totex', ['totex'], file_path, 
                                        Limit=None, New_Pamar=P, New_Setting=S)            
              
              # 2.1.2 Get the ENVEX min undex TOTEX constrained at the current SFF value
            file_path = os.path.join(path, 'point_5.h5')
            S, _ = get_param('settings.csv')
            pt_5_dict[i] = slim_run('limit_totex', ['envex', 'totex'], file_path,
                                   Limit=totex_min_SFF[i]['totex'], 
                                   New_Pamar=P, New_Setting=S) 
            
            
             # 2.1 Pinpoint and solve pareto point 15 on the envex-totex graph
              # 2.2.1 Get the absolute ENVEX minimum
            file_path = os.path.join(path, 'envex_min.h5')
            envex_min[i] = slim_run('envex', ['envex'], file_path, 
                                    Limit=None, New_Pamar=P, New_Setting=S)
            
              # 2.2.2 Get the TOTEX minimu under ENVEX constrained at 7% above the min
            file_path = os.path.join(path, 'point_15.h5')
            pt_15_dict[i] = slim_run('limit_envex', ['envex', 'totex'], 
                                     file_path, Limit=envex_min[i]['envex']*1.073, 
                                     New_Pamar=P, New_Setting=S)    
            
            print(f'Run {i} finished')
        
    return pt_5_dict, pt_15_dict
    
    
    
    
    
    
    
    
    
    
    
 
    
    # print('Solve Time: ', time.time() - start)
    
    
    # # Save all results to a hdf5 file
    # file_name = 'results.h5'
    # cd = results.make_path(objective=objective, Limit=Limit, Pareto=Pareto)
    # path = os.path.join(cd, file_name)
    # results.save_df_to_hdf5(var_results, var_meta, path, Days, Hours, Periods)

    
    # S, _ = get_param('settings.csv')


if __name__ == "__main__":
    # Execute single run
    # run('envex', Reload=True)
    # run('totex', Plot=True, Summary=True)
    # run('envex')

    
    # Execute multi_run
    # pareto('totex', 'envex', 10, Plot=True, Summary=True)
    # pareto('capex', 'opex', 21, Plot=False, Summary=False)
    # pareto('totex', 'envex', 21, Plot=True, Summary=True)
    # diagnostic('totex')
    
    
    #solve_time.append([time.time() - solve_time[i]])
    end = time.time()
    
    print('global runtime: ', end - start, 's')
    # for i in range(10):
    #     print(f'Pareto_{i}_solve_time', solve_time[i] )


def reload_all_inputs():
    """ Reload inputs """
    import write_inputs
    write_inputs.write_arrays('default', Cluster=True)
    
    
def make_results():
    """ Goes through all results in a folder and generate pareto results """
    for p in range(1, 6):
        print(p)
        plot.pareto(f'results\\2020-07-28\\Pareto_{p}')

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




# def pareto(objective_cstr, objective_free, Plot=True, Summary=True):
#     solve_time = []
    
#     # Find the true minimum of objective_cstr
#     path = run(objective_cstr, Pareto=True, Limit=None, Plot=Plot, Summary=Summary)
#     min_obj_cstr = get_objective_value(objective_cstr, path)
#     solve_time.append(time.time() - start)
    
#     # Find the true maximum of objective_cstr
#     path = run(objective_free, Pareto=True, Limit=None, Plot=Plot, Summary=Summary)
#     max_obj_cstr = get_objective_value(objective_cstr, path)
#     solve_time.append(time.time() - start)
    
#     # Generate evenly distributed pareto points
#     # nsteps = 10 # Half of the number of pareto points
#     # epsilon = 1e-6
#     # step = (max_obj_cstr - min_obj_cstr)/(nsteps*2)
#     # Limits_lin = np.arange(min_obj_cstr, max_obj_cstr, step)
#     # Limits = np.concatenate((
#     #     np.linspace(min_obj_cstr*(1 + epsilon), Limits_lin[6], num=nsteps), 
#     #     np.linspace(Limits_lin[6], max_obj_cstr*(1 - epsilon), num=nsteps)[1:-1]))
    
#     nsteps = 6
#     epsilon = 1e-6
#     Limits = np.linspace(min_obj_cstr*(1 + epsilon), max_obj_cstr*(1 - epsilon), 
#                          num=nsteps, endpoint=True)
    
#     # print('\n')
#     # print('min_obj_cstr', min_obj_cstr)
#     # print('max_obj_cstr', max_obj_cstr)
#     # print('Limits_lin', Limits_lin)
#     # print('Limts', Limits)
#     # print('\n')
    
#     # Compute pareto points
#     for i in range(1, len(Limits)):
#         objective = 'limit_' + objective_cstr
#         run(objective, Pareto=True, Limit=Limits[i], Plot=Plot, Summary=Summary)
#         solve_time.append(time.time() - start)
#         plt.close('all')
  
#     # Plot pareto graphs
#     plot.pareto(date=today)












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