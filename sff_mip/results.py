""" This contains all functions necessary get data out of the 'model_data'
    folder and into useable dataframes. 
"""

# External modules
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np


def all_dic(m, Periods):
    var_result_time_indep, var_result_time_dep = {}, {}

    number = np.arange(0, 10).tolist()
    number = [str(n) for n in number]
    
    for v in m.getVars():
        results = []
        if ',0' in v.varName:
            name = v.varName.split(',0')[0]
            for p in Periods:
                results.append(m.getVarByName(name + ',{}]'.format(p)).x)
            var_result_time_dep[name + ']'] = results
        elif '[0' in v.varName:
            name = v.varName.split('[0')[0]
            for p in Periods:
                results.append(m.getVarByName(name + '[{}]'.format(p)).x)
            var_result_time_dep[name] = results
        elif all(n not in v.varName for n in number):
            var_result_time_indep[v.varName] = v.x
            
    return var_result_time_indep, var_result_time_dep


def get_unit_name(var):
    return var.split('[')[1].split(']')[0]

Units_storage = ['BAT']
Color_code = {'BOI': 'firebrick', 'PV': 'aqua', 'BAT': 'navy', 
              'SOFC': 'red', 'AD': 'darkgreen'}
Units = ['BOI', 'PV', 'BAT', 'SOFC', 'AD']


def plot_unit_results(var_result_time_indep, Units, Units_storage, Color_code):
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


def var_time_indep_summary(m, var_result_time_indep, V_meta):
    dic = {}
    for v in var_result_time_indep:
        dic[v] = [m.getVarByName(v).x]
        dic[v] += [m.getVarByName(v).lb, m.getVarByName(v).ub]
        if v in V_meta:
            dic[v] += V_meta[v]
            
    var_result_time_indep['objective'] = m.objVal
    
    df = pd.DataFrame.from_dict(dic, orient='index')
    col = dict(zip([c for c in df.columns], V_meta['Header'][1:]))
    df.rename(columns = col, inplace = True)
    
    return df












"""

vars_name, vars_value, vars_unit, vars_lb, vars_ub = [], [], [], [], []


def time_indep(m, Costs_u):
        Take values and metada of time independent variables (without _t indicator) and return a 
        dataframe of results

    time_indep_var, time_dep_var = var_names(m)
    
    for v in m.getVars(): 
        if v.varName in time_indep_var:
            vars_name.append(v.varName)
            vars_value.append(v.x)
            vars_lb.append(v.lb)
            vars_ub.append(v.ub)

        # Attribute physical units to variables according to differnet criterias
        # By default the units are 'None'
            if v.varName in V_meta:
                vars_unit.append(V_meta[v.varName])
            elif "_size" in v.varName:
                vars_unit.append(Costs_u['Size_units'][v.varName.split('_')[0]])
            elif "_install" in v.varName:
                vars_unit.append('Binary')
            elif "_CAPEX" in v.varName:
                vars_unit.append('kCHF')
            else:
                vars_unit.append(None)
    
    return pd.DataFrame.from_dict(dict_variables)




def plot_time_dep_result(var, all_dic, m, Periods):
    y = all_dic[var]      
    plt.bar(Periods, y)
    
    



dict_variables = {'Variable Name': vars_name, 
                  'Result': vars_value, 
                  'Unit': vars_unit, 
                  'Lower Bound': vars_lb, 
                  'Upper Bound': vars_ub}

"""

##################################################################################################
### END
##################################################################################################
