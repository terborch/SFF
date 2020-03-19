""" This contains all functions necessary get data out of the 'model_data'
    folder and into useable dataframes. 
"""
from matplotlib import pyplot as plt


# Store every variable without the _t indicator (time independent)
def time_indep(m, vars_name, vars_value, vars_unit, vars_lb, vars_ub, dic_vars_unit, U_c):
    
    for v in m.getVars():
        if not "_t" in v.varName:
            vars_name.append(v.varName)
            vars_value.append(v.x)
            vars_lb.append(v.lb)
            vars_ub.append(v.ub)

        # Attribute physical units to variables according to differnet criterias
        # By default the units are 'None'
            if v.varName in dic_vars_unit:
                vars_unit.append(dic_vars_unit[v.varName])
            elif "_size" in v.varName:
                vars_unit.append(U_c['Size_units'][v.varName.split('_')[0]])
            elif "_install" in v.varName:
                vars_unit.append('Binary')
            elif "_CAPEX" in v.varName:
                vars_unit.append('kCHF')
            else:
                vars_unit.append(None)

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

