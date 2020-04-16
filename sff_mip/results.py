""" Getting results out of the model and into dictionnairies or dataframes
    #   all_dic returns two dicts of time depnent or indepenent variable values 
    #   var_time_indep_summary returns a dataframe summarising time indep results
    #   TODO: add V_meta to time dep df
    #   TODO: add lower and upper bound the time dep df
"""

# External modules
import pandas as pd
import numpy as np


def all_dic(m, Periods):
    """ Given the model and periods, returns two dicts.
        1. time independent variable name value pairs
        2. time depenendent variable name value pairs
    """
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


def var_time_indep_summary(m, var_result_time_indep, V_meta):
    """ Given a dict of time independent variable results, returns a summary
        dataframe containing its name, value, lower and upper bound.
        Adds any available metadata from V_meta
        Adds the objective to the dataframe
    """
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


def var_time_dep_summary(m, var_result_time_dep, V_meta):
    """ Given a dict of time dependent variable results, returns a summary
        dataframe containing its name, minimum value, maximum value, average
        and length.
    """
    dic = {}
    for v in var_result_time_dep:
        value = var_result_time_dep[v]
        dic[v] = [min(value), np.mean(value), max(value), len(value)]
    columns = ['Minimum', 'Average', 'Maximum', 'Length']
    df = pd.DataFrame(dic).T
    df.columns = columns
    
    return df


##################################################################################################
### END
##################################################################################################
