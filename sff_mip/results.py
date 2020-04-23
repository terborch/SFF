""" Getting results out of the model and into dictionnairies or dataframes
    #   all_dic returns two dicts of time depnent or indepenent variable values 
    #   var_time_indep_summary returns a dataframe summarising time indep results
    #   TODO: add V_meta to time dep df
    #   TODO: add lower and upper bound the time dep df
    #   TDOD: add exception for SOC to normalize the result from 0 to 1
"""

# External modules
import pandas as pd
import numpy as np

def all_dic(m, Periods, V_bounds):
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
            V_bounds[name + ']'] = [m.getVarByName(name + ',0]').lb, m.getVarByName(name + ',0]').ub]
            for p in Periods:
                results.append(m.getVarByName(name + ',{}]'.format(p)).x)
            var_result_time_dep[name + ']'] = results
        elif '[0' in v.varName:
            name = v.varName.split('[0')[0]
            V_bounds[name] = [m.getVarByName(name + '[0]').lb, m.getVarByName(name + '[0]').ub]
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
        if v in V_meta.keys():
            dic[v] += V_meta[v]
            
    var_result_time_indep['objective'] = m.objVal
    
    df = pd.DataFrame.from_dict(dic, orient='index')
    col = dict(zip([c for c in df.columns], V_meta['Header'][1:]))
    df.rename(columns = col, inplace = True)
    
    return df


def var_time_dep_summary(m, var_result_time_dep, V_meta, V_bounds):
    """ Given a dict of time dependent variable results, returns a summary
        dataframe containing its name, minimum value, maximum value, average
        and length.
    """
    dic = {}
    for v in var_result_time_dep:
        value = var_result_time_dep[v]
        dic[v] = [min(value), np.mean(value), max(value), len(value)]
        dic[v] += V_bounds[v]
        if v in V_meta.keys():
            dic[v] += V_meta[v]
    columns = ['Minimum', 'Average', 'Maximum', 'Length'] + V_meta['Header'][2:]
    df = pd.DataFrame.from_dict(dic, orient='index')
    df.transpose()
    df.columns = columns
    
    return df


def parameters(P, P_meta):
    """ Converts the parameter holder P into a dataframe containing parameter value and metadata
    """
    dic = {}
    Categories = list(P.keys())
    for c in Categories:
        if c == 'Timedep':
            a = 1
        if c == 'Eco':
            a = 1
        else:
            for p in P[c].keys():
                dic[p] = [c]
                dic[p] += [P[c][p]]
                dic[p] += P_meta[c][p]
        columns = ['Category', 'Value', 'Units', 'Description', 'Source']
        df = pd.DataFrame.from_dict(dic, orient='index')
        df.transpose()
        df.sort_values(by=0)
        df.columns = columns
    
    return df



##################################################################################################
### END
##################################################################################################
