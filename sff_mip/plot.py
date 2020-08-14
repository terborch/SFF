""" Plot graphs of results present in result dicts
    #   all_dic returns two dicts of time depnent or indepenent variable values 
    #   var_time_indep_summary returns a dataframe summarising time indep results
    #   TODO: add V_meta to time dep df
    #   TODO: add lower and upper bound the time dep df
"""

# External modules

from matplotlib import pyplot as plt
from matplotlib.pyplot import figure
import numpy as np
import os.path
import pandas as pd
import time
import os
# Internal modules
from read_inputs import (Periods, dt_end, Days, Hours, Ext_T, Irradiance, 
                         Build_cons, Build_T, AD_T, Fueling, Frequence, P)
from global_set import (Units, Units_storage, Resources, Color_code, 
                        Linestyle_code, Linestyles, Abbrev, Unit_color, 
                        G_res, U_prod, U_cons)
import results
from data import get_hdf, get_all_param

###############################################################################
### Global variables to be eliminated
###############################################################################

# Plot settings
fig_width, fig_height = 11.7*2, 5.8

# Converting hourly to daily values
# Day_Dates = []
# Days = (Dates[-1] - Dates[0]).days
# Last_day_hours = int((Dates[-1] - Dates[0]).seconds/3600)
# Days += 1 if Last_day_hours >= 0 else 0
# Day_Dates = [Dates[i*24] for i in range(Days)]
# Day_Dates.append(dt_end)

###############################################################################
### Primary methods
###############################################################################
def plot_value(axis, x_position, value):
    if np.round(value) > 0:
        ysize = axis.get_ylim()[1] - axis.get_ylim()[0]
        axis.text(x_position, value + ysize*0.05, '{:.0f}'.format(value))

def unit_size(path):
    """ Plot a bar chart of the installed capacity of each unit given a path to
        the hdf result file.
    """
    # Split into torage and non storage units
    Names, Values = {}, {}
    Units_ns = list(set(Units) - set(Units_storage))
    Units_ns.sort()
    Names['non_storage'] = [f'unit_size[{u}]' for u in Units_ns]
    Names['storage'] = [f'unit_size[{u}]' for u in Units_storage]
     
    # Only time independent results are used, set names as index
    df = get_hdf(path, 'single')
    df.set_index('Var_name', inplace=True)
    for t in ['non_storage', 'storage']:
        Values[t] = [df.loc[n, 'Value'] for n in Names[t]]   

    # Figure options
    fig, ax1 = plt.subplots()
    plt.title('Installed capacity for each unit')
    fig.set_size_inches(8, 3)
    ax2 = ax1.twinx()
    ax1.set_ylabel('Production capacity in kW')
    ax2.set_ylabel('Storage capacity in kWh')
    ax1.set_xlim(-1, len(Units))
    ax1.set_ylim(0, max(Values['non_storage'])*1.25)
    ax2.set_ylim(0, max(Values['storage'])*1.25)
    
    i = 0
    for n in Names['non_storage']:
        ax1.bar(i, df.loc[n, 'Value'], color='darkgrey')
        plot_value(ax1, i - 0.25, df.loc[n, 'Value'])
        i += 1
    for n in Names['storage']:
        ax2.bar(i, df.loc[n, 'Value'], color='lightgrey')
        plot_value(ax2, i - 0.25, df.loc[n, 'Value'])
        i += 1
                
    # Store the figure in aplt object accessible anywhere
    Names_order = Units_ns + list(Units_storage)
    plt.xticks(range(len(Units)), 
               [Abbrev[Names_order[i]] for i in range(len(Units))])
    fig.autofmt_xdate()
    plt.tight_layout()


def all_results(Per_cent_vary, path):
    """ Plot all time dependent results that vary more than 1%
        # TODO option to plot daily averages only
    """
    
    # Get relevant results into dic
    df = get_hdf(path, 'daily')
    Time_steps = list(range(len(Hours)*len(Days)))
    
    # Get the names of variables that vary more than 1%
    var_name_vary = []
    for n in set(df.index.get_level_values(0)):
        if df[n].max() > Per_cent_vary*df[n].min():
            var_name_vary.append(n)
    var_name_vary.sort()
    
    # Plot each variables and stack them vertically
    fig, axs = plt.subplots(len(var_name_vary), 1, sharex=True)
    fig.set_size_inches(20, 50)
    plt.xlabel('Day')
    fig.subplots_adjust(hspace=0)
    i = 0
    for n in var_name_vary:
        axs[i].plot(Time_steps, df[n], label=n, c=col(n))
        axs[i].legend(loc='upper right')
        axs[i].set_ylabel(get_resource_name(n))
        set_x_ticks(axs[i], Time_steps)
        i += 1
        
    # if daily:
    #     Dates = Day_Dates
    #     var_result = hourly_to_daily_list(var_result, var_name)
        
        
def resource(Resource, Threshold, path):
    
    # Get relevant results into dic
    df = get_hdf(path, 'daily')
    Time_steps = list(range(len(Hours)*len(Days)))
    
    names = []
    for n in set(df.index.get_level_values(0)):
        if Resource in n:
            if df[n].max() >= Threshold or df[n].min() <= -Threshold:
                names.append(n)
    
    nbr_fig = len(names) + 1 if Resource == 'Elec' else len(names)
    
    fig, axs = plt.subplots(nbr_fig, 1, sharex=True)
    fig.set_size_inches(fig_width, fig_height*nbr_fig)
    plt.xlabel('Date')
    fig.subplots_adjust(hspace=0)
    i = 0
    for n in names:
        axs[i].plot(Time_steps, df[n], label=n, c=col(n), ls=ls(n))
        axs[i].legend(loc='upper right')
        axs[i].set_ylabel(get_resource_name(n) + ' in kW')
        i += 1        
    
    if Resource == 'Elec':
        axs[i].plot(Time_steps, np.repeat(Build_cons['Elec'], len(Days)),
                    label='Building consumption', 
                    c=col('Elec'), ls=ls('build'))
        axs[i].legend(loc='upper right')
        axs[i].set_ylabel(get_resource_name(n) + ' in kW')
        
        
    # if daily:
    #     Dates = Day_Dates
    #     var_result = hourly_to_daily_list(var_result, var_name)
    #     Build_cons = hourly_to_daily(Build_cons_Elec)
    # else:
    #     Build_cons = Build_cons_Elec        
    
    
def PV_results(path):
    """ Plot the electricity production of the PV panels agains irradiance 
        # TODO option to plot daily averages only
    """
    
    # Get relevant results into dic
    df = get_hdf(path, 'daily')
    Time_steps = list(range(len(Hours)*len(Days)))
    
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title('PV results')
    ax1.set_xlabel('Dates')
    ax1.set_ylabel('Global Irradiance in kW/m^2')
    set_x_ticks(ax1, Time_steps)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Electricity produced in kW')
    
    n = 'Irradiance'
    ax1.plot(Time_steps, Irradiance.flatten(), label=n, color=col(n))
    n = 'unit_prod[PV][Elec]'
    ax2.plot(Time_steps, df[n].values, label=n, color=col(n), ls=ls(n))

    ax1.legend(loc='center left') 
    ax2.legend(loc='center right')
    
    
    # if daily:
    #     Dates = Day_Dates
    #     Irr = hourly_to_daily(Irradiance)
    #     n = 'unit_prod[PV][Elec]'
    #     var_result[n] = hourly_to_daily(var_result[n])
    # else:
    #     Irr = Irradiance
    
    
def SOFC_results(path):
    """ Plot all variables results relative to  the SOFC """
    # Get relevant results into dic
    df = get_hdf(path, 'daily')
    Time_steps = list(range(len(Hours)*len(Days)))
    
    # Items to plot
    items = {}
    items['name'] = ['unit_prod[SOFC][Elec]', 'unit_cons[SOFC][Gas]', 
                     'unit_cons[SOFC][Biogas]', 'unit_prod[SOFC][Heat]']
    items['label'] = [unit_labels(n) for n in items['name']]
    
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title('SOFC')
    ax1.set_xlabel('Dates')
    ax1.set_ylabel('Resources consumed and produced by the SOFC in kW')
    set_x_ticks(ax1, Time_steps)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Heat produced by the SOFC in kW')
    
    for i, n in enumerate(items['name'][:-1]):
        ax1.plot(Time_steps, df[n], label=items['label'][i], 
                 color=col(n), ls=ls(n)) 
    n = 'unit_prod[SOFC][Heat]'
    ax2.plot(Time_steps, df[n], label=items['label'][-1], 
             color=col(n), ls=ls(n))

    ax1.legend(loc='upper left') 
    ax2.legend(loc='upper right')
    
    
def SOC_results(path):
    """ Plot all variables results relative to  the SOFC """
    
    def set_x_ticks(ax1, Time_steps):
        day_tics = [f'Day {d+1}' for d in range(0,365)]
        ax1.set_xticks(Time_steps[12::24], minor=False)
        ax1.set_xticklabels(day_tics, fontdict=None, minor=False) 
    
    # Get relevant results into dic
    soc = get_hdf(path, 'annual')
    df = get_hdf(path, 'single').set_index('Var_name')['Value']
    Time_steps = list(range(len(Hours)*365))
    
    if max(df[f'unit_size[{n}]'] for n in ['BAT', 'CGT']) <= 0:
        return
    
    # Items to plot
    items = {}
    items['name'] = ['BAT', 'CGT']
    items['label'] = ['Battery SOC', 'Compressed Gas Tank SOC']
    items['resource'] = ['Elec', 'Biogas']
    
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width*10, fig_height)
    plt.title('Storage Normalized State of Charge (SOC)')
    ax1.set_xlabel('Dates')
    ax1.set_ylabel('State of Charge [-]')
    set_x_ticks(ax1, Time_steps)
    
    # Convert the SOC result in kW to percent relative to max capacity
    for i, n in enumerate(items['name']):
        ax1.plot(soc[f'unit_SOC[{n}]']/df[f'unit_size[{n}]'], 
                 label=items['label'][i], color=col(items['resource'][i]), ls=ls(n)) 
    ax1.legend(loc='upper left')
    fig.autofmt_xdate()
    plt.tight_layout()

    

def all_fig(path, save_fig=True):
    
    cd, _ = results.get_directory(path)
    
    unit_size(path)
    print_fig(save_fig, os.path.join(cd, 'installed_capacity.png'))
        
    # unit_temperature(path)
    # print_fig(save_fig, os.path.join(cd, 'temperature_results.png'))
    
    Per_cent_vary = 1.01
    all_results(Per_cent_vary, path)
    print_fig(save_fig, os.path.join(cd, 'all_results.png'))
    
    Threshold = 1e-6
    for r in ['Elec', 'Gas', 'Biogas']:
        resource(r, Threshold, path)
        print_fig(save_fig, os.path.join(cd, f'resource_{r}.png'))
    
    PV_results(path)
    print_fig(save_fig, os.path.join(cd, 'PV.png'))  
        
    SOFC_results(path)
    print_fig(save_fig, os.path.join(cd, 'SOFC.png'))
    
    #flows('v[', 'water flows', 'm^3/h', var_result_time_dep, var_name_time_dep, sort=True, daily=True)
    #print_fig(save_fig, os.path.join(cd, 'Hot_water_flows.png'))
    
    #flows('Heat', 'heat flows', 'kW', var_result_time_dep, var_name_time_dep, sort=True, daily=True)
    #print_fig(save_fig, os.path.join(cd, 'Heat_flows.png'))


def units_and_resources(path, fig_path=None):
    """ Read the result.h5 file in a given result path and plot 4 graphs.
        1. Unit installed capex
        2. Unit investement cost
        3. Emissions by resource + Manure emissions + units total LCA 
        4. Opex by resource + units maintenance
        5. A tiny .csv table with the most important results
        6. A summary of annual resource produced and consumed by each unit
    """
    # fig_path = None
    # list_of_files = [f for f in os.listdir(path) if 'figures' not in f and 'png' not in f]
    # for f in list_of_files:
    #     file_path = os.path.join(path, f)
    #     p = int(f.split('_')[0])
    #     if p in [9, 14, 21]:
    #         units_and_resources(file_path, fig_path)
    
    # Daily values
    if 'results.h5' not in path:
        file_path = os.path.join(path, 'results.h5')
    else:
        file_path = path
        path = os.path.join(*path.split('\\')[:-1])
    df = get_hdf(file_path, 'single')
    df = df.set_index('Var_name')['Value']
    
    # Annual total consumption and production
    df2 = get_hdf(file_path, 'daily')
    df2.sort_index(inplace=True) # Sort for performance
    
    capex = unit_capex(df)
    capacity = unit_capacity(df)
    envex, opex = {}, {}
    for r in G_res:
        # envex[r] = df[f'r_envex[{r}]']
        envex[r] = df[f'r_emissions[{r}]']
        opex[r] = (df[f'grid_import_a[{r}]']*P[r,'Import_cost'] - 
                   df[f'grid_export_a[{r}]']*P[r,'Export_cost'])
        
    envex['Manure'] = 1e3*(P['Farm','Biomass_emissions']*
        (1 - P['Physical','Manure_AD']*df['unit_install[AD]']))
    envex['LCA'] = sum(df[f'unit_size[{u}]']*P[u,'LCA']/P[u,'Life'] 
                                for u in Units)
    opex['Maintenance'] = sum(capex[u]*P[u,'Maintenance'] for u in Units)*1e3
    
    if not fig_path:
        fig_path = path
    else:
        path = fig_path
        
    fig_size = (4,6)
    fig_path = os.path.join(path, 'capacity.png')
    chart_from_dict(capacity, 'Capacity in kW or KWh for storage', 
                    'Installed capacity', fig_size, fig_path=fig_path)
    fig_path = os.path.join(path, 'capex.png')
    chart_from_dict(capex, 'CAPEX contribution in MCHF', 'CAPEX shares', 
                    fig_size, fig_path=fig_path)
    fig_path = os.path.join(path, 'opex.png')
    chart_from_dict(opex, 'OPEX contribution in kCHF/year', 'OPEX shares', 
                    fig_size, fig_path=fig_path)
    fig_path = os.path.join(path, 'envex.png')
    chart_from_dict(envex, 'ENVEX contribution in t-CO2/year', 'ENVEX shares', 
                    fig_size, fig_path=fig_path)
    
    # Make table
    objectives = {
        # 'ENVEX':    [dot(1e3*df['envex']), 't-CO2/year'],
        'ENVEX':    [dot(1e3*df['emissions']), 't-CO2/year'],
        'TOTEX':    [dot(1e3*df['totex']), 'kCHF/year'],
        'OPEX':     [dot(1e3*df['opex']), 'kCHF/year'],
        'CAPEX':    [dot(sum(capex[u] for u in Units)), 'MCHF']
        }
    
    table = pd.DataFrame(objectives).T
    table.rename(columns={0: 'Value', 1: 'Units'}, inplace=True)
    table.to_csv(os.path.join(path, 'summary.csv'))

    # annual = {'prod': {}, 'cons': {}}
    e = 1e-2
    p = {'cons': 1, 'prod': -1}
    annual = {}
    for u in Units:
        for k in ['prod', 'cons']:
            try:
                resources = U_prod[u] if k == 'prod' else U_cons[u]
            except:
                continue
            for r in resources:
                if (sum(df2[f'unit_{k}[{u}][{r}]', d].sum()*
                       Frequence[d] for d in Days) > e):
                    try:
                        annual[k, u, r] = 0
                    except:
                        annual[u] = {}    
                        
                    annual[k, u, r] = p[k]*float(
                        sum(df2[f'unit_{k}[{u}][{r}]', d].sum()*Frequence[d] 
                            for d in Days))*1e-3
                
    for r in G_res:
        for i in ['import', 'export']:
            if df[f'grid_{i}_a[{r}]'] > e:
                k = 'prod' if i == 'import' else 'cons'
                annual[k, 'grid', r] = p[k]*df[f'grid_{i}_a[{r}]']
    
    Unused_res = ['Biomass', 'Biogas', 'Gas', 'Wood', 'Heat', 'Diesel', 'BM']
    for r in Unused_res:
        if df[f'unused_a[{r}]'] > e:
            annual['cons', 'waste', r] = df[f'unused_a[{r}]']
    
    fig_path = os.path.join(path, 'resources.png')
    chart_from_dict(annual, 
                    'Annual total energy in MWh/year',
                    'Annual total energy flows', 
                    fig_size, fig_path=fig_path)
                
def dot(x):
    if np.abs(x) > 10:
        return '{:.0f}'.format(x)
        
    elif np.abs(x) > 1:
        return '{:.1f}'.format(x)
    
    else:
        return '{:.2g}'.format(x)
    
    
def chart_from_dict(y, X_label, Title, fig_size, fig_path=None, e=1e-6):
    """ Draw a horrizontal bar chart of values in a dict 
        Alternatively if the keys of y are tuples, Draw a horrizontal bar 
        chart of values in a dict specifically for annual prod and cons
    """
    fig, ax = plt.subplots()
    fig.set_size_inches(fig_size[0], len(y.keys())*fig_size[1]/16)
    fig.set_dpi(300)
    
    if type(list(y.keys())[0]) != tuple:
        max_val = max([y[k] for k in y.keys()])
        # small_val = any([y[k] > 0 and y[k] < 1 for k in y.keys()])
        for j, k in enumerate(list(y.keys())[::-1]):
            if y[k] > e or y[k] < -e:
                ax.barh(j + 1, y[k], color='grey')
                x_text = y[k] if y[k] > 0 else 0
                ax.text(x_text + 0.01*max_val, j + 1 - 1/len(y.keys()), 
                            dot(y[k]))
        ax.set_yticks(range(1, len(y.keys()) + 1))
        ax.set_yticklabels(list(y.keys())[::-1])
      
    else:
        x_max = max([y[k] for k in y.keys()])
        x_min = min([y[k] for k in y.keys()])
        Delta = 0.01*(x_max - x_min)
        p = {'cons': 1, 'prod': 0}
        
        R = []
        for k in y.keys():
            R.append(k[2])
        
        j = 1
        last_label = None
        Units = []
        for r in set(R) - set(['Biomass']):
           for k in y.keys():
               if r in k:
                   ax.text(y[k]*p[k[0]] + Delta*len(dot(y[k])), 
                           j - 1/len(y.keys()), dot(y[k]))
                   if last_label != r:
                       ax.barh(j, y[k], color=Color_code[r], label=r)
                       last_label = r
                       ax.plot([x_max*1.5, x_min*1.75 ], [j - 0.5]*2, 
                               color='lightgrey', ls='--')
                   else:
                       ax.barh(j, y[k], color=Color_code[r])
                   Units.append(k[1])
                   j = j + 1
    
        ax.set_yticks(range(1, len(Units) + 1))
        ax.set_yticklabels(Units)
        plt.xlim(x_min*1.5, x_max*1.75)
        plt.ylim(0.5, len(Units) + 0.5)  
        plt.legend(loc='center right', fancybox=True, framealpha=0.3)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.title(Title)
    plt.xlabel(X_label)
    plt.tight_layout()

    if fig_path:
        plt.savefig(fig_path)
    else:
        plt.show()
   

def unit_capex(df):
    """ Return a dictionnary containing the capex of each unit for a given
        series of single results. 
    """
    from data import annualize
    from read_inputs import P
    i = P['Farm', 'i']
    capex = {}
    for u in Units:
        capex[u] = df[f'unit_capex[{u}]']/annualize(P[u, 'Life'], i)
    return capex

def unit_capacity(df):
    """ Return a dictionnary containing the capacity of each unit for a given
        series of single results. 
    """
    capacity = {}
    for u in Units:
        if df[f'unit_size[{u}]'] > 0.5:
            capacity[u] = df[f'unit_size[{u}]']
        else:
            capacity[u] = 0
    return capacity

def rename_pareto_run_dir(path, name, new_number):
    """ Change the number infrom of the pareto solution folder."""
    name_chunks = name.split('_')
    name_chunks[0] = f'{new_number}'
    new_name = '_'.join(name_chunks)
    cd_old = os.path.join(path, name)
    cd_new = os.path.join(path, new_name)
    os.rename(cd_old, cd_new)

def dict_to_df_plot(dic):
        """ Turn a dictionnary of results onto a df. Sort along index.
        """
        df = pd.DataFrame.from_dict(dic).T
        df.sort_index(inplace=True)
        idx = [int(i) for i in list(df.index) + np.ones(len(df.index))]
        df['Pareto'] = idx
        df.set_index('Pareto', inplace=True)
        return df
    
def pareto(*args, date=None, print_it=False, Xaxis='totex', Yaxis='envex', 
           Relaxed=True):
    """ Opens the path to the latest pareto folder of results of a given day, 
        alternatively takes a path to that folder.
        - Generate a pareto scatter plot for two given objectives
        - A stacked bar chart of investement cost per unit
        - A floating bar chart to track installed units
        - An interactive parallel coordinates plot .html
        - A txt file summary and timing of the entier run
    """
    
    if args:
        path = args[0]
    else:
        cd = os.path.join('results', date)
        nbr = results.get_last_run_nbr(cd, 'Pareto')
        path = os.path.join(cd, f'Pareto_{nbr}')
        
        # if 'pareto.png' in [f for f in sorted(os.listdir(path))]:
        #     print('Pareto figures already in pareto result folder')
        #     return
    
    def get_pareto_nbr(file_name):
        return int(file_name.split('_')[0])
    
    # path = os.path.join('results', 'Final_results_2020-07-20', 'Pareto_opex_capex_10')
    # path = os.path.join('results', 'Final_results_2020-07-20', 'Pareto_envex_totex_10')
    # path = os.path.join('results', '2020-08-05', 'Pareto_1')
    # path = os.path.join('results', 'Final_results_2020-07-20', 'Pareto_less_cost_PV')
    # path = os.path.join('results', '2020-08-12')

    ### The feed in tariffs functions
    Feed_in_tariff = False
    if Feed_in_tariff:
        path = os.path.join('results', 'Final_results_2020-07-20', 'feed_in_tariffs')
        traiffs = np.linspace(-0.1, 1, 21)[::-1]
     
    """ Get necessary values from pareto reult folders """    
    Pareto = []
    
    list_of_files = [f for f in os.listdir(path) if 'figures' not in f and 'png' not in f]
    for file_name in list_of_files:
        file_path = os.path.join(path, file_name, 'results.h5')
        df = get_hdf(file_path, 'single')
        df.set_index('Var_name', inplace=True)
        if not Feed_in_tariff:
            X, Y = float(df.loc[Xaxis]), float(df.loc[Yaxis])
        else:
            X = float(df.loc[Xaxis])
            Y = traiffs[int(file_name.split('_')[-1]) - 1]
        Pareto.append([file_name, X, Y])

    # Sort the Pareto list along Xaxis
    Pareto.sort(key=lambda sublist: sublist[1]) 
    
    # Remove outliers (first and last solution) and rename their directory
    rename_pareto_run_dir(path, Pareto[0][0], '0')
    rename_pareto_run_dir(path, Pareto[-1][0], '0')
    if Relaxed:
        Pareto = Pareto[1:-1]  

    obj = ['envex', 'totex', 'opex']
    capex, capacity, objectives = {}, {}, {}
    for p, file_name in enumerate([i[0] for i in Pareto]):
        file_path = os.path.join(path, file_name, 'results.h5')
        
        # Only time independent results are used, set names as index
        df = get_hdf(file_path, 'single')
        df.set_index('Var_name', inplace=True)
        capacity[p] = unit_capacity(df['Value'])
        capex[p] = unit_capex(df['Value'])
        objectives[p] = [df['Value'][o] for o in obj]
    
    """ Plot the Pareto scatter graph """ 
    X = [sublist[1] for sublist in Pareto]
    Y = [sublist[2] for sublist in Pareto]
    unit = {'totex': '[MCHF/year]',
            'opex': '[MCHF/year]',
            'capex': '[MCHF/year]',
            'envex': '[kt-CO2/year]'}
    
    # Plot options
    size = (6,5) if len(list_of_files) < 11 else (8,6)
    figure(num=None, figsize=(size), dpi=300, facecolor='w', edgecolor='k')
    if not Feed_in_tariff:
        plt.title('Pareto multi-objective optimization')
        plt.ylabel(f'{Yaxis} in ' + str(unit[Yaxis]))
    plt.xlabel(f'{Xaxis} in ' + str(unit[Xaxis]))
    min_y = min(Y)*0.95 if min(Y) > 0 else min(Y)*1.05
    min_x = min(X)*0.95 if min(X) > 0 else min(X)*1.05
    plt.ylim(min_y, max(Y)*1.05)
    plt.xlim(min_x, max(X)*1.05)
    plt.gca().set_axisbelow(True)
    plt.grid(b=True, which='major', color='lightgrey', linestyle='-')
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    if Feed_in_tariff:
        plt.ylabel('Electricity feed-in tariff in [CHF/kWh]')
        plt.title('Minimum TOTEX relative to feed-in tariffs')
        plt.gca().yaxis.set_ticks(Y)
    
    # # # Add 20 - 80 lines
    # plt.plot([min(X), max(X)], [Dy*0.2 + min(Y)]*2, color='black', ls='--')
    # plt.text(max(X) - Dx*0.3, (Dy*0.2 + min(Y)) + Dy*0.02, '20% more than min opex')
    # plt.plot([Dx*0.2 + min(X)]*2, [min(Y), max(Y)], color='black', ls='--')
    # plt.text((Dx*0.2 + min(X)) + Dx*0.02, max(Y) - Dy*0.05, '20% more than min capex')
    # # plt.scatter(X, Y, marker='o', color='black')    
    
    # Plot pareto point number
    Dx, Dy = (max(X) - min(X)), (max(Y) - min(Y))
    for i, _ in enumerate(X):
        # Text on graph
        plt.text(X[i] - Dx*0.02, Y[i] + Dy*0.01, f'{i + 1}')
        # Rename directories according to the pareto points
        rename_pareto_run_dir(path, Pareto[i][0], i + 1)
    
    plt.scatter(X, Y, marker='o', c=range(len(Pareto)), cmap='plasma')
    plt.tight_layout()
    
    # Save figure
    os.makedirs(os.path.dirname(os.path.join(path, 'figures', '')), exist_ok=True)
    fig_path = os.path.join(path, 'figures')
    plt.savefig(os.path.join(fig_path, 'pareto.png'))
    

    """ Plot the Investement cost bar chart """
    df = dict_to_df_plot(capex)
    plt.rcParams["figure.dpi"] = 300
    ax = df.plot(kind='bar', stacked=True, color=[Unit_color[u] for u in Units])
    ax.set_xlabel('Pareto number')
    ax.set_ylabel('CAPEX in MCHF')
    ax.legend(loc='center left',bbox_to_anchor=(1,0.5))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.title('Shares of investement cost')
    plt.tight_layout()
    plt.savefig(os.path.join(fig_path, 'Investement.png'))
    
    """ Plot the installed capacity floating bar chart """
    fig, ax = plt.subplots()
    for i in df.index:
        for j, u in enumerate(Units[::-1]):
            if df[u][i] > 0:
                ax.barh(j + 1, 0.95, left=i-0.5, color=Unit_color[u])
    ax.set_yticks(range(1, len(Units) + 1))
    ax.set_xticks(range(1, len(df.index) + 1))
    ax.set_yticklabels(Units[::-1])
    ax.set_axisbelow(True)
    ax.grid()
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()
    ax.set_xlim(0.5, len(df.index) + 0.5)
    ax.set_ylim(0.5, len(Units) + 0.5)
    plt.title('Installed technologies')
    plt.xticks(rotation='90')
    plt.yticks()
    plt.xlabel('Pareto number')
    plt.tight_layout()
    plt.savefig(os.path.join(fig_path, 'Installed.png'))
    
    """ Plot the parallel coordinate graph of installed capacity """
    import plotly.graph_objects as go
    df = dict_to_df_plot(capex)
    df_obj = dict_to_df_plot(objectives)
    df_obj.rename(columns={0: 'envex', 1: 'totex', 2: 'opex'}, inplace=True)  
    df_obj['capex'] = df.sum(axis = 1)
    
    df = dict_to_df_plot(capacity)
    df['Pareto'] = list(df.index)
    
    for o in df_obj.columns:
        df[o] = df_obj[o]
        
    Dimentions = []
    for u in list(Units) + list(df_obj.columns) + ['Pareto']:
        if max(df[u]) < 0.5 and u in Units:
            r = [0, 1]
        else:
            r = [0, max(df[u])]
         
        try:
            name = Abbrev[u]
        except:
            name = u
            
        d = 0 if u not in df_obj.columns else 2
        ticks = np.round(np.linspace(0, max(df[u]), num=10, endpoint=True), d)
        Dimentions.append(dict(
            range = r,
            tickvals = ticks,
            label = name, 
            values = df[u],
            visible = True))
    
    fig = go.Figure(data=go.Parcoords(
        line = dict(color = df['Pareto'],
                   showscale = False),
        labelangle = 10,
        labelside  = 'bottom',
        dimensions = Dimentions))
    
    fig.write_html(os.path.join(fig_path, 'parcords.html'))

    plt.clf()


    """ Pareto summary and timing """
    content = []
    for folder in [f for f in os.listdir(path) if 'figures' not in f and 'png' not in f]:
        file_path = os.path.join(path, folder, 'run_info.txt')   
        file_content = []    
        with open(file_path) as txt_file: 
            count = 0
            for line in txt_file: 
                count += 1
                file_content.append(f'Line{count}: {line.strip()}')
        content.append(file_content)
    
    write_time = []
    solve_time = []
    plot_time = []
    warning = False
    for i, c in enumerate(content):
        for line in c:
            if 'Write' in line:
                write_time.append(float(line.split(' ')[-1]))
            if 'Solve' in line:
                solve_time.append(float(line.split(' ')[-1]))
            if 'Plot' in line:
                plot_time.append(float(line.split(' ')[-1]))
            if 'Warning' in line:
                warning = f'Warning in run {i}, high variable value.'
    
    times = np.array(solve_time) + np.array(write_time)
    times.sort()
    
    Summary = """
    For {} pareto optimal solutions the longest solve time was {:.0f} s 
    and the shortest was {:.0f} s. The totale solve and write time was {:.0f} s
    with and average at {:.0f} s. The time solve for each of the three longest 
    runs are {}.
    """.format(len(write_time), max(solve_time), min(solve_time), 
    np.sum(solve_time + write_time), np.mean(solve_time + write_time),
    times[-3:])
    print(Summary)
    # Save info about the run
    file_name = 'summary_info.txt'
    info = {0: f'Number of Runs:                {len(write_time)} s',
            1: f'Average solve and write Time:  {int(np.mean(solve_time + write_time))} s',
            2: f'Total solve and write Time:    {int(np.sum(solve_time + write_time))} s',
            3: f'Solve Time total:              {int(np.sum(solve_time))} s',
            4: f'Write Time total:              {int(np.sum(write_time))} s',
            5: f'Plot Time total:               {int(np.sum(plot_time))} s',
            6: Summary}
    
    with open(os.path.join(fig_path, file_name), 'w') as f:
        for k in info.keys():
            print(info[k], file=f)
            if warning:
                print(warning, file=f)



 
   
def inputs():
    """ Represent all inputs in a few graphs.
        1. Frequency, Temperature and Irradiance are presented once at top
        2. Unit temperatures
        3. Heat consumption
        4. Fuel Consumption
    """
    
    def frequency(ax):
        # Frequency in background
        ax3 = ax.twinx()
        ax3.spines['top'].set_visible(False)
        ax3.axis('off')
        ax3.bar(Time_steps[int(len(Hours)/2)::len(Hours)], Frequence.T[0], 
                alpha=0.15, width=23, color='grey', label='Freuqnecy')
        return ax3
    
    def temperature(ax):
        ax2 = ax.twinx()
        ax2.spines['top'].set_visible(False)
        ax2.set_ylabel('Temperature in °C')
        ax2.step(Time_steps, Ext_T.flatten(), label='Exterior Temperature', 
             color='blue')    
        return ax2
    
    def set_x_ticks(ax1, Time_steps):
        day_tics = [f'Day {d+1}' for d in Days]
        ax1.set_xticks(Time_steps[12::24], minor=False)
        ax1.set_xticklabels(day_tics, fontdict=None, minor=False) 
    
    Time_steps = list(range(len(Hours)*len(Days)))
    fig_width, fig_height = 11.7*2, 5.8
    
    """ Weather and Frequency """
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    set_x_ticks(ax1, Time_steps)
    ax2 = ax1.twinx()
    
    ax1.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    
    plt.title('Weather and Frequency of each of typical day')
    ax1.set_xlabel('Clustered Days')
    ax1.set_ylabel('Temperature in °C')
    ax2.set_ylabel('Global Irradiance in kW/m^2')
    
    ax3 = frequency(ax1)
    position = [f + 1 for f in Frequence.T[0]]
    position[2:-2] = [f/2 for f in Frequence.T[0][2:-2]]
    for i, f in enumerate(Frequence.T[0]):
        ax3.text(Time_steps[int(len(Hours)/2)::len(Hours)][i], position[i],
                 int(f), horizontalalignment='center')
    
    ax1.step(Time_steps, Ext_T.flatten(), label='Exterior Temperature', 
             color='blue')    
    ax2.step(Time_steps, Irradiance.flatten(), label='Irradiance', color='red')
    ax1.legend(loc='upper left') 
    ax2.legend(loc='upper right')
    ax3.legend(loc='upper center')
    
    def reduce(ax, percent):
        ax.set_ylim(ax.get_ylim()[0], ax.get_ylim()[1]*percent)
    reduce(ax1, 1.2)
    reduce(ax2, 1.2)
    reduce(ax3, 1.1)

    
    
    """ Unit Temperatures """
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    set_x_ticks(ax1, Time_steps)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    plt.title('Weather and Frequency of each of typical day')
    ax1.set_xlabel('Clustered Days')
    ax1.set_ylabel('Temperature in °C')
    ax3 = frequency(ax1)
    
    ax1.step(Time_steps, Ext_T.flatten(), label='Exterior Temperature', 
             color='blue')  
    ax1.scatter(Time_steps, Build_T.flatten(), label='Building Tempreature', 
              color='black', s = 5)
    ax1.scatter(Time_steps, AD_T.flatten(), label='AD Temperature', 
              color='green', s = 5)
    
    ax1.legend()
    
    
    
    
    """ Electric Consumption in a day """
    Profile = Build_cons['Elec'].T[0]
    fig, ax1 = plt.subplots()
    ax1.spines['right'].set_visible(False)
    ax1.spines['top'].set_visible(False)
    plt.step(Hours, Profile, where='post', c='blue')
    plt.title('Instant Electric Consumption')
    plt.ylabel('Electric Consumption in kW')
    plt.xlabel('Time of the day in Hours')       
    plt.xticks(Hours[::2])
    plt.ylim(0,250)
    plt.show()



    """ Heat Consumption in a year """ 
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title('Heat Consumption')
    ax1.spines['top'].set_visible(False)
    
    ax1.set_xlabel('Clustered Days')
    ax1.set_ylabel('Building Heat consumption in kW')
    set_x_ticks(ax1, Time_steps)
    
    # Frequency in background
    ax3 = frequency(ax1)
    ax2 = temperature(ax1)
    n = 'Building Heat Consumption'
    ax1.step(Time_steps, Build_cons['Heat'].flatten(), label=n, c='red')
    # n = 'AD Heat Consumption'
    # ax2.step(Time_steps, AD_cons_Heat.flatten(), label=n, c='green')
    
    ax1.legend(loc='upper center')
    ax2.legend(loc='upper right')
    plt.show()
    
    
    """ Fuel consumption """
    title = 'Fuel Consumption'
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title(title)
    ax1.spines['top'].set_visible(False)
    ax1.set_xlabel('Clustered Days')
    ax1.set_ylabel('Fuel consumption in kW')
    set_x_ticks(ax1, Time_steps)
    ax2 = temperature(ax1)
    ax3 = frequency(ax1)
    n = 'Fuel Consumption'
    ax1.step(Time_steps, Fueling.flatten(), label=n, c='black')
    
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.show()
    
    
    
def clustering(Number_of_clusters):
    
    # A list of dates in day/month format
    D = 365
    import pandas as pd
    from datetime import datetime
    datelist = pd.date_range(datetime.strptime('2019-01-01', '%Y-%m-%d'), periods=D).tolist()
    D_list, M_list = [0]*D, [0]*D
    for d in range(D):
        D_list[d] = f'{datelist[d].day}/{datelist[d].month}'
        M_list[d] = f'{datelist[d].strftime("%b")}'
    
    
    import data
    Days = range(D)
    path = os.path.join('inputs', 'clusters.h5')
    Clusters = get_hdf(path, Series=True)
    n = f'Cluster_{Number_of_clusters}'
    Clusters[n] = list(Clusters[n].astype(int))
    Labels, Closest = Clusters[n][:D], Clusters[n][D:]
    Clusters_order = data.arrange_clusters(Labels)
    Clustered_days = data.reorder(Closest, Clusters_order)
    Frequence = data.get_frequence(Labels)
    Frequence = data.reorder(Frequence, Clusters_order)
    
    
    S, _ = data.get_param('settings.csv')
    filename = 'meteo_Liebensberg_10min.csv'
    epsilon = 1e-6
    Ext_T, Irr, _ = data.weather_param(filename, epsilon, 
                                       (Days, Hours), S['Time'])
    
    Ext_T_cls = data.cluster(Ext_T, Clustered_days, Hours)
    Irr_cls = data.cluster(Irr, Clustered_days, Hours)

    def repeat(Values, Frequence):
        """ Return a liste of repeated values by frequencies """
        List = []
        for i, f in enumerate(Frequence):
            List.append([Values[i]]*int(f))
        List = [item for sublist in List for item in sublist]
        return List
    
    Ext_T_cls = repeat(np.mean(Ext_T_cls, axis=1), Frequence)
    Irr_cls = repeat(np.mean(Irr_cls, axis=1), Frequence)
     
    def set_axis():
        """ Set xlabel to 'Date'
            Set xticks as months    
            Remove splines
            Add legend and autoformat layout
        """
        ax.set_xlabel('Date')
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        plt.xticks(Days[::31], M_list[::31])
        plt.legend()
        fig.tight_layout()
        fig.autofmt_xdate()
        
    
    """ Daily average Irradiance """    
    fig, ax = plt.subplots()
    plt.title('Clustering results - Irradiance')
    c = 'red'
    ax.set_ylabel('Daily average Irradiance in kW/m^2')
    ax.plot(Days, np.mean(Irr, axis=1), c=c, alpha=0.3, label='Measured')
    ax.step(Days, Irr_cls, where='post', c=c, label='Clustered')   
    set_axis()
    plt.show()
    
    """ Daily average Temperature """ 
    fig, ax = plt.subplots()
    plt.title('Clustering results - Temperature')
    c = 'blue'
    ax.set_ylabel('Daily average Temperature in °C')
    ax.plot(Days, np.mean(Ext_T, axis=1), c=c, alpha=0.3, label='Measured')
    ax.step(Days, Ext_T_cls, where='post', c=c, label='Clustered')
    set_axis()
    plt.show()
    
    """ Daily average electric grid emissions """
    from read_inputs import Elec_CO2 as Elec_CO2_cls
    Elec_CO2_cls = repeat(np.mean(Elec_CO2_cls, axis=1), Frequence)
    
    file = 'swiss_grid_elec_emissions_2015.csv'
    df = data.open_csv(file, 'profiles', ',')
    df.drop(columns=['info'], inplace=True)
    data.to_date_time(df, 'Date', dt_format='%m/%d/%y %I:%M %p')
    Elec_CO2 = data.reshape_day_hour((df.values), *(range(365),range(24)))
    
    fig, ax = plt.subplots()
    plt.title('Swiss electric grid emissions')
    c = 'black'
    ax.set_ylabel('Daily average emissions in kg-CO2/kWh')
    ax.plot(Days, np.mean(Elec_CO2, axis=1), c=c, alpha=0.3, label='Measured')
    ax.step(Days, Elec_CO2_cls, where='post', c=c, label='Clustered')
    set_axis()
    plt.show()
    
    
    """ Monthly average heat load """
    from read_inputs import Build_cons
    Q_b_model = Build_cons['Heat']
    Q_b_real = [224.5, 263.5, 240.4, 161, 75.5, 56.4, 
                0, 0, 31, 230.3, 211.2, 186]
    Days_in_month = [31,28,31,30,31,30,31,31,30,31,30,31]
    Q_b_real = [(i/j/24*1000) for i, j in zip(Q_b_real, Days_in_month)]
    Q_b_real = repeat(np.array(Q_b_real), np.array(Days_in_month))
    
    Q_b_cls = repeat(np.mean(Q_b_model, axis=1), Frequence)
    
    fig, ax = plt.subplots()
    plt.title('SFF heat load profile')
    c = 'red'
    ax.set_ylabel('Average building heat load in kW-heat')
    ax.plot(Days, Q_b_real, c=c, alpha=0.3, label='Measured')
    ax.step(Days, Q_b_cls, where='post', c=c, label='Clustered')
    set_axis()
    plt.show()
        

def sensitivity_analysis():
    """ Plot a sorted bar chart of the sesitivity analysis """
    folder_path = os.path.join('results', 'sensitivity_analysis')
    list_of_files = [f for f in os.listdir(folder_path) if 'solution' not in f]
    result_files = ['point_5', 'point_15']
    
    P, P_meta = get_all_param()
    variation = P_meta['Uncertainty']
    name = P_meta['Full name']
    default_index = ('all', 'default', '1')
    
    index = ['Solution', 'Param Category', 'Param Name', 'Variation']
    columns = ['envex', 'totex', 'opex', 'capex', 'size'] + [u + ' Size' for u in Units]
    vari_df = pd.DataFrame(columns=columns + index)
    vari_df.set_index(index, inplace=True)
    capex_u = {}
    for f in list_of_files:
        print(f)
        for r in result_files:
            # Read a signle resuts file in one folder
            file_path = os.path.join(folder_path, f, f'{r}.h5')
            df = get_hdf(file_path, 'single')
            df = df.set_index('Var_name')['Value']
            # Make an index i to store information in dict 
            # i = (Pareto point, Category, Name, Change)
            name_index = f.split('_')
            i = (r.split('_')[-1],
                 name_index[0], '_'.join(name_index[1:-1]), name_index[-1])
            if 'default' in f:
                i = (r.split('_')[-1], *default_index)
            capex_u[i] = unit_capex(df)
            capacity = unit_capacity(df)
            vari_df.loc[i] = [1e3*df['envex'], # envex
                              1e3*df['totex'], # totex
                              1e3*df['opex'],  # opex
                              np.sum([capex_u[i][k] for k in capex_u[i].keys()]), # capex
                              0,               # size
                              *[capacity[u] for u in Units] # units 
                              ]
            
    def print_pareto(df, fig_size):
        """ Generate a Pareto graph of results """
        
        fig, ax = plt.subplots()
        fig.set_dpi(300)
        
        for sol in ['5', '15']:
            col = {'5': 'darkviolet', '15': 'gold'}
            plt.scatter(df['totex'].loc[sol,:]*1e-3, df['envex'].loc[sol,:]*1e-3,
                        color=col[sol], zorder=500, label=f'Solution {sol}')
        plt.legend()
        
        """ Add Pareto background """    
        path = os.path.join('results', 'Final_results_2020-07-20', 'Pareto_envex_totex_10')
        Xaxis, Yaxis = 'totex', 'emissions'    
        Pareto = []
        list_of_files = [f for f in os.listdir(path) 
                         if 'figures' not in f and 'png' not in f and '.h5' not in f]
        for file_name in list_of_files:
            file_path = os.path.join(path, file_name, 'results.h5')
            df2 = get_hdf(file_path, 'single')
            df2.set_index('Var_name', inplace=True)
            X, Y = float(df2.loc[Xaxis]), float(df2.loc[Yaxis])
            Pareto.append([file_name, X, Y])

        Pareto = Pareto[1:-1]  
        X = [sublist[1] for sublist in Pareto]
        Y = [sublist[2] for sublist in Pareto]
        plt.scatter(X, Y, marker='o', color='black')# c=range(len(Pareto)), cmap='plasma')

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        plt.xlabel('TOTEX in [MCF/year]')
        plt.ylabel('ENVEX in [kt-CO2/year]')
        plt.ylim(0.15, 0.31)
        plt.xlim(0.31, 0.64)
        plt.title('Variation on solutions 5 and 15')
        plt.tight_layout()
            
        fig_name = '{}.png'.format(Title.replace(' ','_'))
        fig_path = os.path.join(folder_path, f'solution {sol}', fig_name)
        plt.savefig(fig_path)
        
        
    def table():
        """ Table of values changed """
        list_of_files = [f for f in os.listdir(folder_path) 
                     if 'solution' not in f and '.h5' not in f and 'default' not in f]
        file_path = os.path.join('inputs', 'sensitivity_param.csv')
        
        from data import get_param
        P, P_meta = get_param('latex_param.csv')
        P_eco, P_meta_eco = get_param('latex_param_eco.csv')
        P = P.append(P_eco)
        P_meta = P_meta.append(P_meta_eco)
        
        d = {}
        for f in list_of_files:
            Name_split = f.split('_')
            i = (Name_split[0], '_'.join(Name_split[1:-1]))
            vary = float(f.split('_')[-1])
            vary = vary - 1 if vary > 1 else 1 - vary 
            value = float(P[i])
            Full_name = P_meta['Full name'].loc[i]
            Symbol = P_meta['Latex_symbol'].loc[i]
            Variation = '${:.0f}'.format(vary*100) + r'\%$'
            Minima = '${:.2g}$'.format((1 + vary)*value)
            Maxima = '${:.2g}$'.format((1 - vary)*value)
            d[i] = [Full_name, Symbol, Variation, Minima, Maxima]
            
        table = pd.DataFrame.from_dict(d).T
        table.columns = ['Full Name', 'Symbol', 'Variation', 'Minima', 'Maxima']
        table.to_csv(file_path)
        
        
    def units_installed(df):
        """ Returns the list of installed units as array of 1 and 0 """
        return np.array([int(bool(df[f'{u} Size'])) for u in Units])
    
    def get_variation(index):
        """ Return the exact variation for a given file index """
        if 'default' in index:
            return 1
        if float(index[-1]) > 1:
            return 1 + variation[index[:-1]]
        else:
            return 1 - variation[index[:-1]]
        
    def plot_relative_changes(change, colors, Title, x_label, fig_size):
            fig, ax = plt.subplots()
            # fig.set_size_inches(fig_size[0], len(change.index)*fig_size[1]/24)
            fig.set_dpi(300)
            j = 1
            inputs_changed = []
            # ax.plot([0, 0], [0.5, len(vary.index)/2 + 0.5], color ='black')
            for k in change.index:
                # per cent change in result divided by per cent change in input
                
                color = colors[1] if change.loc[k]['increased'] < 0 else colors[0]
                ax.barh(j, np.abs(change.loc[k]['increased']), color=color, height=0.8)
                
                color = colors[1] if change.loc[k]['reduced'] < 0 else colors[0]
                ax.barh(j, -np.abs(change.loc[k]['reduced']), color=color, height=0.8)  
                
                j = j + 1
                if pd.isna(name[k[:-1]]):
                    n = k[1]
                elif k[0] in ['Pysical', 'Farm', 'Profile'] or k[0] in Resources:
                    n = name[k[:-1]]
                else:
                    n = ' '.join([k[0], name[k[:-1]]])
                inputs_changed.append('{} {:.0f}%'.format(n, float(k[-1])*100))
                
            ax.axvline(linewidth=1, color='black', zorder=100)
            # ax.axhline(y= linewidth=1, color='grey', zorder=0,  linestyle="--")
            # plt.axhline(y=1.0, color="black",)
            ax.set_yticks(range(1, len(inputs_changed) + 1))
            ax.set_yticklabels(inputs_changed)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.title(Title)
            plt.xlabel(x_label)
            plt.tight_layout()
            
            fig_name = '{}.png'.format(Title.replace(' ','_'))
            fig_path = os.path.join(folder_path, f'solution {sol}', fig_name)
            plt.savefig(fig_path)
       
            
    # for every solution create a df
    for sol in ['5', '15']:
        print(f'printing for solution {sol}')
        default = vari_df.loc[(sol, *default_index),:]
        change_df = vari_df.loc[sol, :, :, :]
        Units_index = [u + ' Size' for u in Units]
        os.makedirs(os.path.dirname(os.path.join(folder_path, f'solution {sol}', '')), exist_ok=True)
        
        # Cumulative change in installed capacity
        Size_max = [change_df[f'{u} Size'].max() for u in Units]
        for k in change_df.index:
            delta = change_df[Units_index].loc[k] - default[Units_index]
            count = 0
            if all(delta == 0):
                change_df['size'].loc[k] = 0
                continue
            for i, u in enumerate(Units_index):
                if Size_max[i] != 0:
                    count = count + (delta[Units_index[i]]/Size_max[i])**2
            change_df['size'].loc[k] = count**0.5/np.abs(get_variation(k) - 1)
        
        # for every objective create series of results that vary
        for o in change_df.columns:
            vary = change_df[o]
            Title = 'Variation on ' + o
            # Sort from largest to smallest variation
            change = pd.DataFrame(columns=['increased', 'reduced', 'delta'] + index[1:])
            change.set_index(index[1:], inplace=True)
            for k in vary.index:
                if get_variation(k) < 1:
                    continue
                v1, v2 = get_variation(k), 1 - (get_variation(k) - 1)
                k1 = tuple(list(k[:-1]) + ['{:.2g}'.format(v1)])
                k2 = tuple(list(k[:-1]) + ['{:.2g}'.format(v2)])
                key = tuple(list(k[:-1]) + ['{:.2g}'.format(get_variation(k) - 1)])
                if k2 not in vary.index:
                    continue
                if o != 'size':
                    relative1 = (vary[k1]/default[o] - 1) / (v1 - 1)
                    relative2 = (vary[k2]/default[o] - 1) / (v2 - 1)
                else: 
                    relative1 = change_df['size'][k1]
                    relative2 = change_df['size'][k2]
                    
                if np.abs(relative1) > 0.001 or np.abs(relative2) > 0.001:
                    change.loc[key] = [relative1, relative2, np.abs(relative1) + np.abs(relative2)]
            change.sort_values('delta', ascending=True, inplace=True)
            
    
            colors = ('green', 'red') if o != 'size' else ('grey', 'grey')
            x_label = ('%change output over %change input' if o != 'size' else
                       'agregated change in installed capacity')
            fig_size = (6.4, 4.8)
            plot_relative_changes(change[-10:], colors, Title, x_label, fig_size)
        
        
 

            

def plot_mc():
    path = os.path.join('results', 'monte_carlo')

    
    """ Get necessary values from pareto reult folders """    
    Pareto = []
    
    list_of_files = [f for f in os.listdir(path) if 'figures' not in f and 'png' not in f]
    
    
    obj = ['envex', 'totex']
    capacity, objectives = {}, {}
    for p, file_name in enumerate(list_of_files):
        file_path = os.path.join(path, file_name, 'results.h5')
        # Only time independent results are used, set names as index
        try:
            df = get_hdf(file_path, 'single')
        except:
            continue
        df.set_index('Var_name', inplace=True)
        capacity[p] = unit_capacity(df['Value'])
        objectives[p] = [df['Value'][o] for o in obj]
    
    table = pd.DataFrame.from_dict(capacity).T
    obj_df = pd.DataFrame.from_dict(objectives).T
    obj_df = obj_df.rename(columns={0: 'envex', 1:'totex'})
    
    
    
    
    for u in Units:
        size = (8,6)
        figure(num=None, figsize=(size), dpi=300, facecolor='w', edgecolor='k')
        plt.title(u + ' Probability distribution of Size')
        table[u].hist()

        
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.xlabel('Installed capacity in kW or kWh')
        plt.ylabel('Number of occurences')
        plt.tight_layout()
    
    
    size = (8,6)
    figure(num=None, figsize=(size), dpi=300, facecolor='w', edgecolor='k')
    obj_df.plot.scatter('totex', 'envex', color='black')

    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.xlabel('TOTEX in [MCHF/year]')
    plt.ylabel('ENVEX in [kt-CO2/year]')
    plt.tight_layout()


    def renamethem():
        def renameitfast(path, file_name, new_number):
            name_chunks = file_name.split('_')
            name_chunks[1] = f'{new_number}'
            new_name = '_'.join(name_chunks)
            cd_old = os.path.join(path, file_name)
            cd_new = os.path.join(path, new_name)
            os.rename(cd_old, cd_new)
        
        # rename files
        numbers = range(500,6000)
        for i, f in enumerate(list_of_files):
            renameitfast(path, f, numbers[i])





    
    
###############################################################################
### Secondairy methods
###############################################################################


def get_resource_name(var_name):
    """ Get the abbreviated name of a resoucre from a variable name string """
    name = []
    for r in Resources:
        if r in var_name:
            name.append(r)
    if not name:
        name.append('default')
    return(name[0])
        
def get_unit_name(var_name):
    """ Get the abbreviated name of a unit from a variable name string """
    name = []
    for u in Units:
        if f'[{u}]' in var_name:
            name.append(u)
    if not name:
        name.append('default')
    return(name[0])

def col(var_name):
    """ Return the color code of a corresponding resource """
    r = get_resource_name(var_name)
    return Color_code[r]

def ls(var_name):
    """ Return the linestyle code of a corresponding unit """
    u = get_unit_name(var_name)
    if Linestyle_code[u] in Linestyles.keys():
        return Linestyles[Linestyle_code[u]]
    else:
        return Linestyle_code[u]

def print_fig(save_fig, cd):
    """ Either display or save the figure to the specified path, then close the figure. """
    if save_fig:
        try:
            plt.savefig(cd)
            print(f'Figure saved at {cd}')
        except:
            print(f'Empty figure could not be saved at {cd}')
    else:
        plt.show()
    plt.clf()
    

def set_x_ticks(ax1, Time_steps):
    day_tics = [f'Day {d+1}' for d in Days]
    ax1.set_xticks(Time_steps[12::24], minor=False)
    ax1.set_xticklabels(day_tics, fontdict=None, minor=False)  
    

def unit_labels(unit_name):
    l = unit_name.split('_')[1].split('[')
    return '{} {} {}'.format(l[1][:-1], l[0], l[2][:-1])


def make_patch_spines_invisible(ax):
    for p in ['top', 'right', 'left']:
        ax.spines[p].set_visible(False)

###############################################################################
### END
###############################################################################
