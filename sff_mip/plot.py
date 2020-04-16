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
from initialize_model import Periods
from global_param import Date, Ext_T, Irradiance, Build_cons_elec
from global_set import Units, Units_storage

Color_code = {'BOI': 'firebrick', 'PV': 'aqua', 'BAT': 'navy', 'build_T': 'black', 'Ext_T': 'blue',
              'SOFC': 'orange', 'AD': 'darkgreen', 'Irradiance': 'red', 'bat_SOC': 'purple'}

def col(name):
    if '[' in name:
        name = get_unit_name(name)
    return Color_code[name]


def unit_results(var_result_time_indep):
    """ Given a dictionnary of time independent results plot a bar chart of the size of units
        in kW of production capacity for non-storage units and in kWh for storage units.
    """

    fig, ax1 = plt.subplots()
    plt.title('Installed capacity for each unit')
    ax2 = ax1.twinx()
    ax1.set_ylabel('Installed production capacity in kW')
    ax2.set_ylabel('Installed storage capacity in kWh')
    
    names = {}
    i, j = 0, len(Units) - len(Units_storage)
    for var in var_result_time_indep:
        if 'size' in var:
            name = get_unit_name(var)
            value = var_result_time_indep[var]
            if name not in Units_storage:
                ax1.bar(i, value)
                names[i] = name
                i += 1
            else:
                ax2.bar(j, value, color = Color_code[name])
                names[j] = name
                j += 1
                
    plt.xticks(range(len(Units)), [names[i] for i in range(len(Units))])


def resource(resource, var_result, var_name):
    fig, ax1 = plt.subplots()
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Electricity exchanged with units in kW')
    ax2 = ax1.twinx()
    ax2.set_ylabel('Electricity exchanged with the grids and buildings in kW')

    for name in var_name:
        if resource in name:
            if 'grid' not in name:
                if 'prod' in name:
                    ax1.plot(Date, var_result[name], label = name)
                else:
                    ax1.plot(Date, [var_result[name][p]*(-1) for p in Periods], label = name)
            else:
                if 'import' in name:
                    ax2.plot(Date, var_result[name], label = name, linestyle='--')
                else:
                    ax2.plot(Date, [var_result[name][p]*(-1) for p in Periods], label = name, linestyle='--')
    
    if resource == 'Elec':
        ax2.plot(Date, Build_cons_elec, label = 'Building consumption', linestyle='--')
        

    ax1.legend(loc='center left') 
    ax2.legend(loc='center right')


def temperature_results(var_result):
    fig, ax1 = plt.subplots()
    plt.title('Weather and building temperatures')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Temperature in °C')
    ax2 = ax1.twinx()
    ax2.set_ylabel('Global Irradiance in kW/m^2')
    
    name = 'build_T'
    ax1.plot(Date, var_result[name], label = name, color=col(name))
    name = 'unit_T[AD]'
    ax1.plot(Date, var_result[name], label = name, color=col(name))
    name = 'Ext_T'
    ax1.plot(Date, Ext_T, label = name, color=col(name))
    
    name = 'Irradiance'
    ax2.plot(Date, Irradiance, label=name, color=col(name))

    ax1.legend(loc='center left') 
    ax2.legend(loc='center right')


def get_unit_name(var):
    """ Return the units name from a variable string string """
    return var.split('[')[1].split(']')[0]


def PV_results(var_result, Irradiance):
    fig, ax1 = plt.subplots()
    plt.title('PV')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Electricity produced in kW')
    ax2 = ax1.twinx()
    ax2.set_ylabel('Global Irradiance in kW/m^2')
    
    name = 'prod[PV][Elec]'
    ax1.plot(Date, var_result[name], label = name, color=col(name))
    name = 'Irradiance'
    ax2.plot(Date, Irradiance, label=name, color=col(name), linestyle='--')

    ax1.legend(loc='center left') 
    ax2.legend(loc='center right')
    

def SOFC_results(var_result):
    fig, ax1 = plt.subplots()
    plt.title('SOFC')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Resources consumed and produced by the SOFC in kW')
    ax2 = ax1.twinx()
    ax2.set_ylabel('Heat produced by the SOFC in kW')
    
    name = 'prod[SOFC][Elec]'
    ax1.plot(Date, var_result[name], label = name, color=col(name))
    name = 'cons[SOFC][Gas]'
    ax1.plot(Date, var_result[name], label = name, color=col(name), linestyle='--')
    name = 'cons[SOFC][Biogas]'
    ax1.plot(Date, var_result[name], label = name, color=col(name), linestyle='--')
    
    name = 'prod[SOFC][Heat]'
    ax2.plot(Date, var_result[name], label=name, color=col(name), linestyle='-.')

    ax1.legend(loc='upper left') 
    ax2.legend(loc='upper right')


def normalize(l):
    return [l[i]/max(l) for i in range(len(l))]

def all_results(var_result, var_name, cd):
    fig, ax1 = plt.subplots()
    plt.xlabel('Date')
    plt.ylabel('Variation')
    
    for v in var_name:
        if max(var_result[v]) > min(var_result[v])*1.1:
            variation = normalize(var_result[v])
            plt.title(v)
            plt.plot(Date, variation, label = v)
            plt.savefig(os.path.join(cd, 'all_results_{}.png'.format(v)))
            plt.clf()
    



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


def flows(indicator, name, units, var_result_time_dep, sort = False):
    plt.title(name)
    plt.xlabel('Date')
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
    
    # Transpose the list of flows
    flows_T_sort = list(map(list, zip(*flows_sort)))
    plt.plot(Date, flows_T_sort)
    plt.legend(flows_name_sort)

##################################################################################################
### END
##################################################################################################
