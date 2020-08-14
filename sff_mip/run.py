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
from data import get_param, get_all_param

start_construct = time.time()

# Internal modules
import model
import results
import plot

from read_inputs import Periods, Days, Hours

today = datetime.now().strftime("%Y-%m-%d")

end_construct = time.time()
print('model construct time: ', end_construct - start_construct, 's')


def run(objective, Reload=False, Relax=False, Pareto=False, Limit=None,
        Plot=True, Summary=True, Save_txt=False,New_Pamar=None, New_Setting=None):
    """ Solve the optimization model once then store the result in hdf5 format.
        # TODO save inputs into the resut folder
    """
    # Option to generate a new input.h5 file 
    if Reload:
        import write_inputs
        write_inputs.write_arrays('default', Cluster=True)
    
    start_solve = time.time()
    # Select objective and solve the model
    m = model.run(objective, Relax=Relax, Limit=Limit, New_Pamar=None, New_Setting=None)
    
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
    plot.units_and_resources(path, fig_path=None)
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


def relax(minimum, r):
    """ Relax a given minimum by a factor r """
    if minimum > 0:
        return minimum*(1 + r)
    elif minimum < 0:
        return minimum*(1 - r)
    elif minimum == 0:
        return minimum + r

def pareto(objective_x, objective_y, N_points, Plot=True, Summary=True,
           Dirty_and_fast=False):
    
    
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
    path = run('limit_' + objective_y, Pareto=True, Limit=relax(min_y, r), 
               Plot=Plot, Summary=Summary)
    min_y = get_objective_value(objective_y, path)
    max_x = get_objective_value(objective_x, path)
    solve_time.append(time.time() - start)
    

    # Find the true maximum of objective_y
    path = run('limit_' + objective_x, Pareto=True, Limit=relax(min_x, r), 
               Plot=Plot, Summary=Summary)
    min_x = get_objective_value(objective_x, path)
    max_y = get_objective_value(objective_y, path)
    solve_time.append(time.time() - start)
        
    # List of pareto results
    x = [min_x, max_x]
    y = [max_y, min_y]
    
    if not Dirty_and_fast:
        # add n new pareto points to the x, y list
        for i in range(N_points - 2):
            # Longest segment number
            s = np.argmax(disctance(x, y)) + 1
            # Objective according to slope
            obj = choose_objective(x[s], x[s-1], y[s], y[s-1])
            # Insert new point in the middle of the longest segment
            make_point(s, obj, x, y)
    
    elif Dirty_and_fast:
        N_points = N_points - 1
        
        Change_frequency = max_x*0.3
        
        Limits_1 = np.linspace(min_x, Change_frequency, int(np.ceil(N_points/2)), endpoint=False)[1:]
        Limits_2 = np.linspace(Change_frequency, max_x, int(np.ceil(N_points/2)), endpoint=False)
        Limits = np.concatenate((Limits_1, Limits_2))
        
        print('\n', '***********', Limits, '***********', '\n')
        for l in Limits:
            path = run('limit_' + objective_x, Pareto=True, Limit=l, Plot=Plot, Summary=Summary)
            solve_time.append(time.time() - start)
            plt.close('all')
            
        
    # Plot pareto graphs
    plot.pareto(date=today, Xaxis=objective_x, Yaxis=objective_y)
    
    # plt.scatter(x,y)
    max_y = 0.0806278045309544
    min_x = 0.265086379422707
    min_y = -0.0888118110670387
    max_x = 1.22181371114481
    
def diagnostic(objective):
    """ Run the model with one of each heating system only """
    from global_set import U_res, Units
    import data
    import read_inputs
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


def slim_run(objective, querry, *file_path, Relax=False,
             Limit=None, New_Pamar=None, New_Setting=None):
    """ Minimalistic run function, solve the model with given inputs
        and returns a name-value dictionnary for each item in the querry list
        Saves all results in a hdf5 file to the specified path.
    """
    # Solve the model
    m = model.run(objective, Limit=Limit, Relax=Relax,
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
    
    # file_name = 'run_info.txt' 
    # with open(os.path.join(file_path[0], file_name), 'w') as f:
    #     for v in m.getVars():
    #         if v.x > 2000:
    #             print('Warning high variable value', file=f)
    #             print('{}: {:.0f}'.format(v.VarName, v.x), file=f)
        
    return m, Querried_results


def make_folder(param_index, variation, folder_path):
    """ Create a new folder inside folder_path based on the Param_index
        and variation. Return a path to the new folder. """
    
    param_name = '_'.join(param_index)
    new_folder = '_'.join([param_name, '{:.2g}'.format(variation)])

    os.makedirs(os.path.dirname(os.path.join(folder_path, new_folder, '')), 
                exist_ok=True)
    
    return os.path.join(folder_path, new_folder)
    
    
def sensitsivity_analysis():
    """ Performs a sensitivity analysis on the selected parameters using the 
        One At a Time approach.
    """
    folder_path = os.path.join('results', 'sensitivity_analysis')
    list_of_files = [f for f in os.listdir(folder_path)]
    path_separator = os.path.join('a', 'a').split('a')[1]
    
    # 1. Select what parameter to modify and use this new value as input.
    P, P_meta = get_all_param()
    variation = P_meta['Uncertainty']
    totex_min_SFF, envex_min = {}, {}
    pt_5_dict, pt_15_dict = {}, {}
    for i in variation[variation > 0].index:
        print(i, '{:.2g}'.format(P[i]*(1 + variation[i])), '{:.2g}'.format(P[i]), 
              '{:.2g}'.format(P[i]*(1-variation[i])))
        
        # Reset all input parameters to default values
        P, _ = get_all_param()
        for p in [1, -1]:
            # Param index i, Positivie or Negative p, Variation variation[i]
            P[i] = P[i]*(1 + p*variation[i])
            
            path = make_folder(i, 1 + p*variation[i], folder_path)
            if path.split(path_separator)[-1] in list_of_files:
                continue
            # 2. Run the optimizer with a new parameter value
             # 2.1 Pinpoint and solve pareto point 5 on the envex-totex graph
              # 2.1.1 Get the TOTEX min for the current SFF scenario
            file_path = os.path.join(path, 'current_SFF.h5')
            S, _ = get_param('settings_SFF_current.csv')
            _, totex_min_SFF[i] = slim_run('totex', ['totex'], file_path, 
                                        Limit=None, New_Pamar=P, New_Setting=S)            
              
              # 2.1.2 Get the ENVEX min undex TOTEX constrained at the current SFF value
            file_path = os.path.join(path, 'point_5.h5')
            S, _ = get_param('settings.csv')
            pt_5_dict[i] = slim_run('limit_totex', ['envex', 'totex'], file_path,
                                   Limit=totex_min_SFF[i]['totex'], 
                                   New_Pamar=P, New_Setting=S) 
            
            
             # 2.2 Pinpoint and solve pareto point 15 on the envex-totex graph
              # 2.2.1 Get the absolute ENVEX minimum
            file_path = os.path.join(path, 'envex_min.h5')
            _, envex_min[i] = slim_run('envex', ['envex'], file_path, 
                                    Limit=None, New_Pamar=P, New_Setting=S)
            
              # 2.2.2 Get the TOTEX minimu under ENVEX constrained at 7% above the min
            file_path = os.path.join(path, 'point_15.h5')
            pt_15_dict[i] = slim_run('limit_envex', ['envex', 'totex'], 
                                     file_path, Limit=envex_min[i]['envex']*1.073, 
                                     New_Pamar=P, New_Setting=S)    
            
            print(f'Run {i} finished')
    

    # # No variation - default run
    # path = make_folder(['default'], 1, folder_path)
    # P, _ = get_all_param()
    #  # 2.1 Pinpoint and solve pareto point 5 on the envex-totex graph
    #   # 2.1.1 Get the TOTEX min for the current SFF scenario
    # file_path = os.path.join(path, 'current_SFF.h5')
    # S, _ = get_param('settings_SFF_current.csv')
    # totex_min_SFF[i] = slim_run('totex', ['totex'], file_path, 
    #                             Limit=None, New_Pamar=P, New_Setting=S)            
      
    #   # 2.1.2 Get the ENVEX min undex TOTEX constrained at the current SFF value
    # file_path = os.path.join(path, 'point_5.h5')
    # S, _ = get_param('settings.csv')
    # pt_5_dict[i] = slim_run('limit_totex', ['envex', 'totex'], file_path,
    #                        Limit=totex_min_SFF[i]['totex'], 
    #                        New_Pamar=P, New_Setting=S) 
    
    
    #  # 2.2 Pinpoint and solve pareto point 15 on the envex-totex graph
    #   # 2.2.1 Get the absolute ENVEX minimum
    # file_path = os.path.join(path, 'envex_min.h5')
    # envex_min[i] = slim_run('envex', ['envex'], file_path, 
    #                         Limit=None, New_Pamar=P, New_Setting=S)
    
    #   # 2.2.2 Get the TOTEX minimu under ENVEX constrained at 7% above the min
    # file_path = os.path.join(path, 'point_15.h5')
    # pt_15_dict[i] = slim_run('limit_envex', ['envex', 'totex'], 
    #                          file_path, Limit=envex_min[i]['envex']*1.073, 
    #                          New_Pamar=P, New_Setting=S)  

    
    return pt_5_dict, pt_15_dict
    
    
    
    
    
 
    
    # print('Solve Time: ', time.time() - start)
    
    
    # # Save all results to a hdf5 file
    # file_name = 'results.h5'
    # cd = results.make_path(objective=objective, Limit=Limit, Pareto=Pareto)
    # path = os.path.join(cd, file_name)
    # results.save_df_to_hdf5(var_results, var_meta, path, Days, Hours, Periods)

    
    # S, _ = get_param('settings.csv')


def pareto_incentive(objective, incentives):
    """ Run the model with one of each heating system only """
    from global_set import U_res, Units
    import data
    import read_inputs
    
    for i in incentives:
        data.change_settings('Farm', 'Feed_in_tariff', i, file='settings_palezieux.csv') 
        reload(read_inputs)
        reload(model)
        run(objective)
        plt.close('all')
        data.change_settings('Farm', 'Feed_in_tariff', 0.28, file='settings_palezieux.csv') 



def palezieux(Reload=False, Reference=False, Plot=True, Summary=True):
    """ Alters parameters that concern the case study for Palézieux """
    
    
    if Reload:
        P , _ = get_all_param()
        P_heat_load, _ = get_param('heat_load_param.csv')
        P = P.append(P_heat_load)
        P_new, _ = get_param('palezieux_param.csv')
        
        # Parma pre-calculation
         # Inside write_inputs => calc_param.csv
        f = 'Farm'
        P[f, 'cons_Elec_annual'] = 1e3*P_new[f, 'cons_Elec_annual']
        P[f, 'cons_Heat_annual'] = 1e3*(P_new[f, 'cons_heat'] + P_new[f, 'export_heat'])
         # Inside heal_loads_cals => heat_load_param.csv
        P['AD', 'LSU'] = P_new[f, 'Cows']
        P['build', 'Heated_area'] = P_new[f, 'A_heated']
    
        path = os.path.join('inputs', 'inputs_palezieux.h5')
        reload_all_inputs(path, Cluster=True, New_Pamar=P, New_Setting=None)


    # Plot=True
    # Summary=True
    # file_path = os.path.join('results', 'palezieux')
    # pareto('totex', 'envex', 21, Plot=Plot, Summary=Summary)
    
    # Palezieux Reference scenario
    if Reference:
        # S, _ = get_param('settings.csv')
        # S, _ = get_param('settings_Palezieux_current.csv')
        # S, _ = get_param('settings.csv')
        folder_path = os.path.join('results', 'palezieux_test_totex_7')
        os.makedirs(os.path.dirname(os.path.join(folder_path, '')), 
                exist_ok=True)
        
        file_path = os.path.join(folder_path, 'results.h5')
        m, obj = slim_run('totex', ['envex', 'totex'], file_path, Relax=False, 
                       Limit=None, New_Pamar=None, New_Setting=None)
        
        m, obj = slim_run('limit_totex', ['envex', 'totex'], file_path, Relax=False, 
               Limit=0.1, New_Pamar=None, New_Setting=None)
        
        plot.units_and_resources(folder_path)
    print(obj)
    
    
def reload_all_inputs(path='default', Cluster=True, 
                      New_Pamar=None, New_Setting=None):
    """ Reload inputs """
    import write_inputs
    write_inputs.write_arrays(path, Cluster=True,
                              New_Pamar=New_Pamar, New_Setting=New_Setting)

    
def make_results():
    """ Goes through all results in a folder and generate pareto results """
    for p in range(1, 6):
        print(p)
        plot.pareto(f'results\\2020-07-28\\Pareto_{p}')


def monte_carlo(Plot=False):
    import pandas as pd
    from global_set import Units
    
    folder_path = os.path.join('results', 'monte_carlo')
    list_of_files = [f for f in os.listdir(folder_path)]
    path_separator = os.path.join('a', 'a').split('a')[1]
    
    # 1. Select what parameter to modify and use this new value as input.
    P, P_meta = get_all_param()
    variation = P_meta['Uncertainty']

    # index discarded from the analysis
    P_vary = variation[variation > 0]
    drop_index = []
    # for i in P_vary.index:
    #     if i[0] in Units and 'Cost_multiplier' not in i:
    #         drop_index.append(i)
            
    # Monte carlo parameters
    Pmc = P_vary.drop(drop_index)        
    
    index = ['Iteration', 'Category', 'Name']
    columns = ['Value', 'Lower bound', 'Upper bound']
    mc_df = pd.DataFrame(columns=columns + index)
    mc_df.set_index(index, inplace=True)
    
    Iterations = range(200, 500)
    for i in Pmc.index:
        Upper = P[i]*(1 + Pmc[i])
        Lower = P[i]*(1 - Pmc[i])
        mu, sigma = P[i], P[i]*Pmc[i]/3
        print(i)
        for j in Iterations:
            value = np.random.default_rng().normal(mu, sigma)
            mc_df.loc[j, i[0], i[1]] = [value, '{:.2g}'.format(Upper), '{:.2g}'.format(Lower)]
            
    obj = {}
    for i in Iterations:
        # Make new path, continue if path already exist
        path = os.path.join(folder_path, f'mc_{int(i)}')
        os.makedirs(os.path.dirname(os.path.join(path, '')), 
                    exist_ok=True)
        

        if path.split(path_separator)[-1] in list_of_files:
            continue
        
        # Attribute new values to parameters
        Param = mc_df.loc[(mc_df.index.get_level_values('Iteration') == i)].droplevel(0)
        P[Param.index] = Param['Value']

        # Run and save results
        file_path = os.path.join(path, 'results.h5')
        Param.to_csv(os.path.join(path, 'Parameters.csv'))
        obj[i] = slim_run('totex', ['envex', 'totex', 'opex', 'capex'], file_path,
                                   Limit=None, 
                                   New_Pamar=P, New_Setting=None)

        
 
        
        
        
       
    if Plot:
        import matplotlib.pyplot as plt
        
        for i in Pmc.index:
            Upper = P[i]*(1 + Pmc[i])
            Lower = P[i]*(1 - Pmc[i])
            mu, sigma = P[i], P[i]*Pmc[i]/3
            # mean and standard deviation
            s = np.random.default_rng().normal(mu, sigma, 2500)
            
            count, bins, ignored = plt.hist(s, 30, density=True)
            plt.plot(bins, 1/(sigma * np.sqrt(2 * np.pi)) *
                           np.exp( - (bins - mu)**2 / (2 * sigma**2) ),
                     linewidth=2, color='r')
            plt.title(i)
            plt.axvline(x=Upper)
            plt.axvline(x=Lower)
            plt.show()

    
    
if __name__ == "__main__":
    
    
    # palezieux(Reload=False, Reference=False, Plot=True, Summary=True)
    
    # Execute single run
    # run('envex', Reload=True)
    # run('totex', Plot=True, Summary=True)
    
    
    # pareto_incentive('totex', np.linspace(0.3, 0.4, 10))
    
    
    # pareto_incentive('totex', np.linspace(1, 5, 10))
    
    # run('totex', Plot=True, Summary=True)
    
    # run('envex')
    
    
    # Execute multi_run
    # pareto('totex', 'envex', 10, Plot=True, Summary=True)
    # pareto('capex', 'opex', 21, Plot=False, Summary=False)
    
    
    # pareto('totex', 'envex', 21, Plot=False, Summary=False, Dirty_and_fast=False)
    
    
    # diagnostic('totex')
    
    
    #solve_time.append([time.time() - solve_time[i]])
    end = time.time()
    
    print('global runtime: ', end - start, 's')
    # for i in range(10):
    #     print(f'Pareto_{i}_solve_time', solve_time[i] )




def matrix_coefficients(m):
    rows = [m.getRow(c) for c in m.getConstrs()]
    for row in rows:
        coeffs = {row.getVar(i).varname: row.getCoeff(i) for i in range(row.size())}
    return coeffs

    extreme_coeff = {}
    for c in m.getConstrs():
        r = m.getRow(c)
        coeff = [r.getCoeff(i) for i in range(r.size())]
        if any([np.abs(c) > 0 and np.abs(c) < 5e-7 for c in coeff]):
            extreme_coeff[c.ConstrName] = coeff
            
    extreme_coeff = []
    for c in m.getConstrs():
        r = m.getRow(c)
        coeff = [r.getCoeff(i) for i in range(r.size())]
        if any([np.abs(c) > 0 and np.abs(c) < 1e-2 for c in coeff]):
            extreme_coeff.append([c.ConstrName, c])
            
    extreme_coeff
    
    
def understanding_what_the_hell_is_going_on(m):
    """ Function to study a givem mip model m. usefeull whenever nothing works,
    but requiers a solution. Try reducing the model and increasing ( then reducing) 
    constraints until at least a solution is produced then study it here.
    Pro-tips: set a small time limit for solve time once the solver hit it, 
    it will return an intermeediary solution.
    """
    
    for v in m.getVars():
        if v.x > 2000 :
            print(v.varName, v.x)
            
    for v in m.getVars():
        if np.abs(v.x) > 17 and np.abs(v.x) < 20:
            print(v.varName, v.x)
            
    for v in m.getVars():
        if np.abs(v.x) == 10:
            print(v.varName, v.x)
            
    extreme_coeff = []
    for c in m.getConstrs():
        r = m.getRow(c)
        coeff = [r.getCoeff(i) for i in range(r.size())]
        if any([np.abs(c) > 0 and np.abs(c) < 1e-7 for c in coeff]):
            extreme_coeff.append([c.ConstrName, c])
            
    extreme_coeff    
    
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