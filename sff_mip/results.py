""" This contains all functions necessary get data out of the 'model_data'
    folder and into useable dataframes. 
"""

# External modules
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
# Internal modules
from initialize_model import V_meta

vars_name, vars_value, vars_unit, vars_lb, vars_ub = [], [], [], [], []


def time_indep(m, Costs_u):
    """ Take values and metada of time independent variables (without _t indicator) and return a 
        dataframe of results
    """
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


def var_names(m):
    time_indep_var, time_dep_var   = [], []
    number = np.arange(0, 10).tolist()
    number = [str(n) for n in number]
    
    # get all variable names, store the time dependent ones and cut the period index
    for v in m.getVars():
        if ',0' in v.varName:
            time_dep_var.append(v.varName.split(',0')[0])
        elif '[0' in v.varName:
            time_dep_var.append(v.varName.split('[0')[0])
        elif all(n not in v.varName for n in number):
            time_indep_var.append(v.varName)
                   
    return time_indep_var, time_dep_var  


def plot_time_dep_result(var, all_dic, m, Periods):
    y = all_dic[var]      
    plt.bar(Periods, y)
    
    
def get_all_var(m, vars_name_t, Periods):
    time_indep_dic = {}
    time_dep_dic = {}
    
    time_indep_dic['objective'] = m.objVal
    for v in m.getVars():
        if not '0' in v.varName:
            time_indep_dic[v.varName] = v.x
    
    for v in m.getVars():
        results = []
        if ',0' in v.varName:
            name = v.varName.split(',0')[0]
            for p in Periods:
                results.append(m.getVarByName(name + ',{}]'.format(p)).x)
            time_dep_dic[name + ']'] = results
        elif '[0' in v.varName:
            name = v.varName.split('[0')[0]
            for p in Periods:
                results.append(m.getVarByName(name + '[{}]'.format(p)).x)
            time_dep_dic[name] = results
        
    return time_indep_dic, time_dep_dic


dict_variables = {'Variable Name': vars_name, 
                  'Result': vars_value, 
                  'Unit': vars_unit, 
                  'Lower Bound': vars_lb, 
                  'Upper Bound': vars_ub}


##################################################################################################
### END
##################################################################################################
