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
from initialize_model import Periods, dt_end
from global_param import Dates, Ext_T, Irradiance, Build_cons_Elec
from global_set import (Units, Units_storage, Resources, Color_code, Linestyle_code, Linestyles,
                        Abbrev)

# Plot settings
fig_width, fig_height = 11.7*2, 5.8

# Converting hourly to daily values
Day_Dates = []
Days = (Dates[-1] - Dates[0]).days
Last_day_hours = int((Dates[-1] - Dates[0]).seconds/3600)
Days += 1 if Last_day_hours >= 0 else 0
Day_Dates = [Dates[i*24] for i in range(Days)]
Day_Dates.append(dt_end)

def get_resource_name(var_name):
    """ Get the abbreviated name of a resoucre from a variable name string """
    name = []
    for r in Color_code.keys():
        if r in var_name:
            name.append(r)
    if not name:
        name.append('default')
    return(name[0])
        
def get_unit_name(var_name):
    """ Get the abbreviated name of a unit from a variable name string """
    name = []
    for u in Linestyle_code.keys():
        if u in var_name:
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


def unit_results(var_result_time_indep, var_name_time_indep, title=None):
    """ Given a dictionnary of time independent results plot a bar chart of the size of units
        in kW of production capacity for non-storage units and in kWh for storage units.
    """

    fig, ax1 = plt.subplots()
    if title:
        plt.title(title)
    else:
        plt.title('Installed capacity for each unit')
    ax2 = ax1.twinx()
    ax1.set_ylabel('Installed production capacity in kW')
    ax2.set_ylabel('Installed storage capacity in kWh')
    
    names = {}
    i, j = 0, len(Units) - len(Units_storage)
    for var_name in var_name_time_indep:
        if 'size' in var_name:
            name = get_unit_name(var_name)
            value = var_result_time_indep[var_name]
            if name not in Units_storage:
                ax1.bar(i, value, color='darkgrey')
                names[i] = name
                i += 1
            else:
                ax2.bar(j, value, color='grey')
                names[j] = name
                j += 1

    plt.xticks(range(len(Units)), [names[i] for i in range(len(Units))])


def resource(resource, var_result, var_name, Dates, daily=False):
    
    if daily:
        Dates = Day_Dates
        var_result = hourly_to_daily_list(var_result, var_name)
        Build_cons = hourly_to_daily(Build_cons_Elec)
    else:
        Build_cons = Build_cons_Elec
    
    name = []
    for n in var_name:
        if resource in n:
            name.append(n)
    
    nbr_fig = len(name) + 1 if resource == 'Elec' else len(name)
    
    fig, axs = plt.subplots(nbr_fig, 1, sharex=True)
    fig.set_size_inches(fig_width, fig_height*nbr_fig)
    plt.xlabel('Date')
    fig.subplots_adjust(hspace=0)
    i = 0
    for n in name:
        axs[i].plot(Dates, var_result[n], label=n, c=col(n), ls=ls(n))
        axs[i].legend()
        axs[i].set_ylabel(get_resource_name(n) + ' in kW')
        i += 1        
    
    if resource == 'Elec':
        axs[i].plot(Dates, Build_cons, label = 'Building consumption', c=col('Elec'), 
                    ls=ls('build'))
        axs[i].legend()
        axs[i].set_ylabel(get_resource_name(n) + ' in kW')
        

def temperature_results(var_result):
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title('Building and unit temperatures')
    ax1.set_xlabel('Dates')
    ax1.set_ylabel('Temperature in °C')
    ax2 = ax1.twinx()
    ax2.set_ylabel('Global Irradiance in kW/m^2')
    
    n = 'build_T'
    ax1.plot(Dates, var_result[n], label='Building Temperature', color=col(n), ls=ls(n))
    n = 'unit_T[AD]'
    ax1.plot(Dates, var_result[n], label='AD Temperature', color=col(n), ls=ls(n))
    n = 'Ext_T'
    ax1.plot(Dates, Ext_T, label='External Temperature', color=col(n), ls=ls(n))
    
    n = 'Irradiance'
    ax2.plot(Dates, Irradiance, label=n, color=col(n))

    ax1.legend(loc='center left') 
    ax2.legend(loc='center right')


def PV_results(var_result, Irradiance, Dates, daily=False):
    
    if daily:
        Dates = Day_Dates
        Irr = hourly_to_daily(Irradiance)
        n = 'unit_prod[PV][Elec]'
        var_result[n] = hourly_to_daily(var_result[n])
    else:
        Irr = Irradiance
        
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title('PV')
    ax1.set_xlabel('Dates')
    ax1.set_ylabel('Global Irradiance in kW/m^2')
    ax2 = ax1.twinx()
    ax2.set_ylabel('Electricity produced in kW')
    
    name = 'Irradiance'
    ax1.plot(Dates, Irr, label=name, color=col(name))
    name = 'unit_prod[PV][Elec]'
    ax2.plot(Dates, var_result[name], label=name, color=col(name), ls=ls(name))

    ax1.legend(loc='center left') 
    ax2.legend(loc='center right')


def SOFC_results(var_result):
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title('SOFC')
    
    
    ax1.set_xlabel('Dates')
    ax1.set_ylabel('Resources consumed and produced by the SOFC in kW')
    ax2 = ax1.twinx()
    ax2.set_ylabel('Heat produced by the SOFC in kW')
    
    n = 'unit_prod[SOFC][Elec]'
    ax1.plot(Dates, var_result[n], color=col(n), ls=ls(n))
    n = 'unit_cons[SOFC][Gas]'
    ax1.plot(Dates, var_result[n], color=col(n), ls=ls(n))
    n = 'unit_cons[SOFC][Biogas]'
    ax1.plot(Dates, var_result[n], color=col(n), ls=ls(n))
    
    n = 'unit_prod[SOFC][Heat]'
    ax2.plot(Dates, var_result[n], color=col(n), ls=ls(n))

    ax1.legend(loc='upper left') 
    ax2.legend(loc='upper right')


def normalize(l):
    return [l[i]/max(l) for i in range(len(l))]


def all_results(var_result, var_name, Dates, daily=False):
    """ Plot all time dependent results that vary more than 1%"""
    if daily:
        Dates = Day_Dates
        var_result = hourly_to_daily_list(var_result, var_name)
    
    var_name_vary = []
    for n in var_name:
        if max(var_result[n]) > 1.01*min(var_result[n]):
            var_name_vary.append(n)
            
    fig, axs = plt.subplots(len(var_name_vary), 1, sharex=True)
    fig.set_size_inches(20, 50)
    plt.xlabel('Date')
    fig.subplots_adjust(hspace=0)
    i = 0
    for n in var_name_vary:
        axs[i].plot(Dates, var_result[n], label=n, c=col(n))
        axs[i].legend()
        axs[i].set_ylabel(get_resource_name(n))
        i += 1


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


def transpose_list(l):
    """ Returns the transpose of a given list. """
    return list(map(list, zip(*l)))


def flows(indicator, name, units, var_result_time_dep, sort = False):
    fig, ax = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title(name)
    plt.xlabel('Dates')
    plt.ylabel(name + units)
    # Get relevant flows according to indicator
    flows, flows_name = [], []
    for n in var_result_time_dep:
        if indicator in n:
            flows.append(var_result_time_dep[n])
            flows_name.append(n)
    # Sort in decreasing order each flow by maximum value
    if sort:
        flows_sort = sort_from_index(flows, sorted_index(flows))
        flows_name_sort = sort_from_index(flows_name, sorted_index(flows))
    else: flows_sort, flows_name_sort = flows,  flows_name
    
    
    for f, n in zip(flows_sort, flows_name_sort):
        plt.plot(Dates, f, ls=ls(n))
    plt.legend(flows_name_sort)


def print_fig(save_fig, cd):
    """ Either display or save the figure to the specified path, then close the figure. """
    if save_fig:
        plt.savefig(cd)
    else:
        plt.show()
    plt.clf()


##################################################################################################
### END
##################################################################################################



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