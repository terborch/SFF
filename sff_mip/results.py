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
import re


def get_all(m, Days, Hours, Periods):
    """ Get all results from the gurobi model m into a dictionnary split in time dependent and
        time independent variables. Get the upper and lower bounds of each variable in a dict.
        Return both dictionnarairies.
    """
    var_names_cut = set()
    for v in m.getVars():
        name = re.split('\d', v.VarName)[0]
        var_names_cut.add(name)
    
    var_results, var_bounds = ({'time_indep': {}, 'time_dep':{}} for i in range(2))
    x = lambda v: [v.lb, v.ub]
    for n in var_names_cut:
        results = []
        Time_steps = 'Daily' if 'CGT' not in n else 'Annual'
        if n[-1] == ',' or n[-1] == '[':
            key = 'time_dep'
            if Time_steps == 'Daily':
                results = [[m.getVarByName(n + f'{d},{h}]').x for h in Hours] for d in Days]
                bounds = x(m.getVarByName(n + '0,0]'))
            elif Time_steps == 'Annual':
                results = [m.getVarByName(n + f'{p}]').x for p in Periods]
                bounds = x(m.getVarByName(n + '0]'))
            n = n[:-1] + ']' if n[-1] == ',' else n[:-1]
        else:
            key = 'time_indep'
            results = m.getVarByName(n).x
            bounds = x(m.getVarByName(n))
            
        var_bounds[key][n] = bounds
        var_results[key][n] = results
    return var_results, var_bounds


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


def var_time_dep_summary(m, var_result_time_dep, V_meta, var_bounds):
    """ Given a dict of time dependent variable results, returns a summary
        dataframe containing its name, minimum value, maximum value, average
        and length.
    """
    dic = {}
    for v in var_result_time_dep:
        value = var_result_time_dep[v]
        dic[v] = [min(value), np.mean(value), max(value), len(value)]
        dic[v] += var_bounds[v]
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
            pass
        if c == 'Eco':
            pass
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
