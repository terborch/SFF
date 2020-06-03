""" Plot graphs of results present in result dicts
    #   all_dic returns two dicts of time depnent or indepenent variable values 
    #   var_time_indep_summary returns a dataframe summarising time indep results
    #   TODO: add V_meta to time dep df
    #   TODO: add lower and upper bound the time dep df
"""

# External modules
from matplotlib import pyplot as plt
import numpy as np
import os.path
# Internal modules
from param_input import Periods, dt_end, Days, Hours
from param_calc import Dates, Ext_T, Irradiance, Build_cons, Build_T, AD_T
from global_set import (Units, Units_storage, Resources, Color_code, 
                        Linestyle_code, Linestyles, Abbrev)
import results
from results import var_index

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
   

def unit_size(path):
    """ Plot a bar chart of the installed capacity of each unit given a path to
        the hdf result file.
    """
    # Only time independent results are used, set names as index
    df_result = results.get_hdf(path, 'single')
    df_result.set_index('Var_name', inplace=True)
    var_names = [f'unit_size[{u}]' for u in Units]   

    # Figure options
    fig, ax1 = plt.subplots()
    plt.title('Installed capacity for each unit')
    fig.set_size_inches(8, 3)
    ax2 = ax1.twinx()
    ax1.set_ylabel('Installed production capacity in kW')
    ax2.set_ylabel('Installed storage capacity in kWh')
    
    # Split into torage and non storage units
    Units_non_storage = list(set(Units) - set(Units_storage))
    Units_non_storage.sort()
    i = 0
    for n in [f'unit_size[{u}]' for u in Units_non_storage]:
        ax1.bar(i, df_result.loc[n, 'Value'], color='darkgrey')
        i += 1
    for n in [f'unit_size[{u}]' for u in Units_storage]:
        ax2.bar(i, df_result.loc[n, 'Value'], color='lightgrey')
        i += 1
                
    # Store the figure in aplt object accessible anywhere
    Names_order = Units_non_storage + list(Units_storage)
    plt.xticks(range(len(Units)), [Names_order[i] for i in range(len(Units))])
    

def unit_temperature(path):
    """ Plot the building and AD temperature against externale temperature and
        Irradiance.
        # TODO option to plot daily averages only
    """
    # Get relevant results into dic and shape them into the same shape as Ext_T
    shape = np.shape(Ext_T)
    df = results.get_hdf(path, 'daily')
    
    # Items to plot
    Time_steps = list(range(len(Hours)*len(Days)))
    items = {}
    items['name'] = ['Build_T', 'AD_T', 'Ext_T', 'Irradiance']
    items['value'] = [Build_T, AD_T, Ext_T, Irradiance]
    items['label'] = ['Building Temperature', 'AD Temperature', 
                      'External Temperature', 'Irradiance']
    
    # Plot options 
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title('Building and unit temperatures')
    ax1.set_xlabel('Dates')
    ax1.set_ylabel('Temperature in °C')
    set_x_ticks(ax1, Time_steps)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Global Irradiance in kW/m^2')
    
    # Store plot in plt object
    for i, n in enumerate(items['name'][:-1]):
        ax1.plot(Time_steps, items['value'][i].flatten(), label=items['label'][i], 
                 color=col(n), ls=ls(n))
    n = 'Irradiance'
    ax2.plot(Time_steps, items['value'][3].flatten(), label=n, color=col(n))
    ax1.legend(loc='center left') 
    ax2.legend(loc='center right')
    
    # if daily:
    #     Dates = Day_Dates
    #     for i in range(len(items['value'])):
    #         items['value'][i] = np.mean(items['value'][i], axis=1)


def all_results(Per_cent_vary, path):
    """ Plot all time dependent results that vary more than 1%
        # TODO option to plot daily averages only
    """
    
    # Get relevant results into dic
    df = results.get_hdf(path, 'daily')
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
    df = results.get_hdf(path, 'daily')
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
    df = results.get_hdf(path, 'daily')
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
    df = results.get_hdf(path, 'daily')
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
    

def all_fig(path, save_fig=True):
    
    cd, _ = results.get_directory(path)
    
    unit_size(path)
    print_fig(save_fig, os.path.join(cd, 'installed_capacity.png'))
        
    unit_temperature(path)
    print_fig(save_fig, os.path.join(cd, 'temperature_results.png'))
    
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



###############################################################################
### END
###############################################################################


"""
def flows(indicator, name, units, var_result, var_name, sort=False,  daily=True):
        
    fig, ax = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title(name)
    plt.xlabel('Dates')
    plt.ylabel(name + units)
    # Get relevant flows according to indicator
    flows, flows_name = [], []
    for n in var_result:
        if indicator in n:
            flows.append(var_result[n])
            flows_name.append(n)
    # Sort in decreasing order each flow by maximum value
    if sort:
        flows_sort = sort_from_index(flows, sorted_index(flows))
        flows_name_sort = sort_from_index(flows_name, sorted_index(flows))
    else: flows_sort, flows_name_sort = flows,  flows_name
    
    
    for f, n in zip(flows_sort, flows_name_sort):
        plt.plot(Dates, f, ls=ls(n))
    plt.legend(flows_name_sort)
    
    
    # if daily:
    #     Dates = Day_Dates
    #     var_result = hourly_to_daily_list(var_result, var_name)
    

def hourly_to_daily(hourly_values):
    i, j = 0, 24
    daily_average = []
    for d in range(Days):
        daily_average.append(sum(hourly_values[i:j])/24)
        i, j = 24*d, 24*(1 + d)
    daily_average.append(sum(hourly_values[i:-1])/Last_day_hours)
    return daily_average

def hourly_to_daily_list(var_result, var_name):     
    daily_var_result = {}
    for n in var_name:
        daily_var_result[n] = hourly_to_daily(var_result[n])
    return daily_var_result

def normalize(l):
    return [l[i]/max(l) for i in range(len(l))]

def sorted_index(unsorted_list):
    
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

def transpose_list(l):
    
    return list(map(list, zip(*l)))


"""


""" Returns the transpose of a given list. """
""" Given a list of lists returns an index (lost of pairs) where the first element is 0, 1, 2... n 
        the new index sorted by the largest element in each list in decreasing order. The second element
        is the index of the same list in the original list of list.
"""



"""
def resource(resource, var_result, var_name):
    fig, ax1 = plt.subplots()
    ax1.set_xlabel('Dates')
    ax1.set_ylabel(Abbrev[resource] + ' exchanged with units in kW')
    ax2 = ax1.twinx()
    ax2.set_ylabel(Abbrev[resource] + ' exchanged with grids and buildings in kW')
    ax1.set_xlim(Dates[0], Dates[-1])
    
    for n in var_name:
        if resource in n:
            if 'grid' not in n:
                if 'prod' in n:
                    ax1.plot(Dates, var_result[n], label=n, c=col(n), ls=ls(n))
                else:
                    ax1.plot(Dates, [var_result[n][p]*(-1) for p in Periods], 
                             label=n, c=col(n), ls=ls(n))
            else:
                if 'import' in n:
                    ax2.plot(Dates, var_result[n], label=n, c=col(n), ls=ls(n))
                else:
                    ax2.plot(Dates, [var_result[n][p]*(-1) for p in Periods], 
                             label=n, c=col(n), ls=ls(n))
    
    if resource == 'Elec':
        ax2.plot(Dates, Build_cons_Elec, label = 'Building consumption', c=col('Elec'), ls=ls(n))

    ax1.legend(loc='center left') 
    ax2.legend(loc='center right')
"""   