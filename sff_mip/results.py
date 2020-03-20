""" This contains all functions necessary get data out of the 'model_data'
    folder and into useable dataframes. 
"""

# External modules
from matplotlib import pyplot as plt
import pandas as pd
# Internal modules
from initialize_model import V_meta
vars_name, vars_value, vars_unit, vars_lb, vars_ub = [], [], [], [], []


def time_indep(m, U_c):
    """ Take values and metada of time independent variables (without _t indicator) and return a 
        dataframe of results
    """
    
    for v in m.getVars():
        if not "_t" in v.varName:
            vars_name.append(v.varName)
            vars_value.append(v.x)
            vars_lb.append(v.lb)
            vars_ub.append(v.ub)

        # Attribute physical units to variables according to differnet criterias
        # By default the units are 'None'
            if v.varName in V_meta:
                vars_unit.append(V_meta[v.varName])
            elif "_size" in v.varName:
                vars_unit.append(U_c['Size_units'][v.varName.split('_')[0]])
            elif "_install" in v.varName:
                vars_unit.append('Binary')
            elif "_CAPEX" in v.varName:
                vars_unit.append('kCHF')
            else:
                vars_unit.append(None)
    
    return pd.DataFrame.from_dict(dict_variables)


def time_dep_var_names(m):
    full_list = []
    unique_list = []

    # get all variable names, store the time dependent ones and cut the period index
    for v in m.getVars():
        if "_t" and "," in v.varName:
            full_list.append(v.varName.split(",")[0])
        elif "_t" in v.varName and "," not in v.varName:
            full_list.append(v.varName.split("[")[0])

    # remove repetitions
    for i in full_list:
        if i not in unique_list:
            unique_list.append(i)
    return unique_list 


def plot_time_dep_result(var, all_dic, m, Periods):
    y = all_dic[var]      
    plt.bar(Periods, y)
    
    
def get_all_var(m, vars_name_t, Periods):
    time_indep_dic = {}
    time_dep_dic = {}
    
    time_indep_dic['objective'] = m.objVal
    for v in m.getVars():
        if not "_t" in v.varName:
            time_indep_dic[v.varName] = v.x
    
    for v in vars_name_t:
        res_list = []
        if '[' in v:
            for p in Periods:
                res_list.append(m.getVarByName(v + ',{}]'.format(p)).x)
            time_dep_dic[v + ']'] = res_list
        else:
            for p in Periods:
                res_list.append(m.getVarByName(v + '[{}]'.format(p)).x)
            time_dep_dic[v] = res_list
        
    return time_indep_dic, time_dep_dic


dict_variables = {'Variable Name': vars_name, 
                  'Result': vars_value, 
                  'Unit': vars_unit, 
                  'Lower Bound': vars_lb, 
                  'Upper Bound': vars_ub}


##################################################################################################
### END
##################################################################################################
