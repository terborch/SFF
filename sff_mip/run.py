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

# External modules
import os.path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import time
import numpy as np

start = time.time()

# Internal modules
import results
from initialize_model import m, S, V_meta, V_bounds, P, P_meta, C_meta
from global_param import Costs_u, Periods, Ext_T, Irradiance, Dates
import model
import data
import plot
from plot import fig_width, fig_height



def run_single(objective, relax=False, save_df=True, save_fig=True, big_vars=False):
    

    # Build and run the MIP optimization model
    model.run(objective, relax)
    
    end = time.time()
    print('solve time model: ', end - start, 's')
    
    # Dicts of all variables and their results
    var_result_time_indep, var_result_time_dep = results.all_dic(m, Periods, V_bounds)
    var_name_time_indep = list(var_result_time_indep.keys())
    var_name_time_dep = list(var_result_time_dep.keys())
        
    df_time_indep = results.var_time_indep_summary(m, var_result_time_indep, V_meta)
    df_time_dep = results.var_time_dep_summary(m, var_result_time_dep, V_meta, V_bounds)
    df_parameters = results.parameters(P, P_meta)
    
    # display result summary
    pd.options.display.max_rows = 50
    pd.options.display.max_columns = 10
    pd.set_option('precision', 2)

    print(df_time_indep)
    print(df_time_dep)
    
    matplotlib.rcParams['figure.figsize'] = (fig_width, fig_height)
    plot.unit_results(var_result_time_indep, var_name_time_indep)
    plt.show()
    
    if save_df or save_fig:
        # datetime object containing current date and time
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        cd = os.path.join('results', '{}'.format(today))
        os.makedirs(os.path.dirname(os.path.join(cd, '')), exist_ok=True)
        # list of files present in the current result dirrectory
        files=[]
        files = [f for f in sorted(os.listdir(cd))]
        # increment file name by numbers of run in a day
        runs = []
        for f in files:
            if 'run_nbr' in f:
                runs.append(f)
        if not runs:
            run_nbr = 1
        else:
            run_nbr = max([int(i.split('_')[-1]) for i in runs]) + 1
        
        cd = os.path.join(cd, 'run_nbr_{}'.format(run_nbr), '')
        os.makedirs(os.path.dirname(cd), exist_ok=True)
    
    if save_df:
        df_time_indep.to_csv(os.path.join(cd, 'df_time_indep.csv'))
        df_time_dep.to_csv(os.path.join(cd, 'df_time_dep.csv'))
        df_parameters.to_csv(os.path.join(cd, 'parameters.csv'))
        
    if big_vars:
        with open('vars_above_10k.txt', 'w') as f:
            for v in m.getVars():
                if v.x > 10000:
                    print(v.varName + ': {:.2f}\n'.format(v.x), file=f)
                    
        with open('vars_all.txt', 'w') as f:
            for v in m.getVars():
                    print(v.varName + ': {:.2f}\n'.format(v.x), file=f)
    
    if save_fig:
        plot.unit_results(var_result_time_indep, var_name_time_indep)
        plt.savefig(os.path.join(cd, 'installed_capacity.png'))
        
    plot.temperature_results(var_result_time_dep)
    plot.print_fig(save_fig, os.path.join(cd, 'temperature_results.png'))

    for r in ['Elec', 'Gas', 'Biogas']:
        plot.resource(r, var_result_time_dep, var_name_time_dep, Dates, daily=True)
        plot.print_fig(save_fig, os.path.join(cd, 'resource{}.png'.format(r)))
    
    plot.flows('v[', 'water flows', 'm^3/h', var_result_time_dep, True)
    plot.print_fig(save_fig, os.path.join(cd, 'Hot_water_flows.png'))
    
    plot.flows('Heat', 'heat flows', 'kW', var_result_time_dep, True)
    plot.print_fig(save_fig, os.path.join(cd, 'Heat_flows.png'))
    
    plot.PV_results(var_result_time_dep, Irradiance, Dates, daily=False)
    plot.print_fig(save_fig, os.path.join(cd, 'PV.png'))  
        
    plot.SOFC_results(var_result_time_dep)
    plot.print_fig(save_fig, os.path.join(cd, 'SOFC.png'))

    plot.all_results(var_result_time_dep, var_name_time_dep, Dates, daily=True)
    plot.print_fig(save_fig, os.path.join(cd, 'all_results.png'))


# Execute single run
###run_single('emissions', save_fig=True)

run_single('totex', save_fig=True)


end = time.time()

print('global runtime: ', end - start, 's')

# Dicts of all variables and their results
var_result_time_indep, var_result_time_dep = results.all_dic(m, Periods, V_bounds)
var_name_time_indep = list(var_result_time_indep.keys())
var_name_time_dep = list(var_result_time_dep.keys())


"""
# Execute Pareto optimization
def run_pareto(objective, Limit=None):
    
    # Multiobjective relaxation
    Relaxation = 1+1e-4
    
    # Build and run the MIP optimization model
    if Limit:
        model.run(objective, Limit=Limit*Relaxation)
        print('-----------------{}--------------------'.format(Limit*Relaxation))
    else:
        model.run(objective)
    
    var_result_time_indep, var_result_time_dep = results.all_dic(m, Periods, V_bounds)
    var_name_time_indep = list(var_result_time_indep.keys())
    Results[objective] = var_result_time_indep
    
    plot.unit_results(var_result_time_indep, var_name_time_indep, 
                      title=Objective_description[objective])
    plt.show()

Results = {}

Objective_description = {
    'totex': 'TOTEX minimization', 
    'emissions': 'Emissions minimization',
    'pareto_totex':'Emissions minimization with constrained TOTEX at the minimum',
    'pareto_emissions': 'TOTEX minimization with constrained emissions at the minimum',
    }


objective = 'totex'
run_pareto(objective)
Totex_min = Results[objective][objective]

objective = 'emissions'
run_pareto(objective)
Emissions_min = Results[objective][objective]

objective = 'pareto_totex'
run_pareto(objective, Totex_min)
Emissions_max = Results[objective]['emissions']

objective = 'pareto_emissions'
run_pareto(objective, Emissions_min)
Totex_max = Results[objective]['totex']
"""
##################################################################################################
### END
##################################################################################################
