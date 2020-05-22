""" Getting results out of the model and into dictionnairies or dataframes
    #   get_all returns two dicts of variables values and variable metadata
    #   summmary prints and save 
    #   TODO: add V_meta to time dep df
    #   TODO: add lower and upper bound the time dep df
    #   TDOD: add exception for SOC to normalize the result from 0 to 1
"""

# External modules
import pandas as pd
import numpy as np
import re
import os
from datetime import datetime

###############################################################################
### Global variables to be eliminated
###############################################################################


vtypes = {'C': 'continuous', 
          'B': 'binary', 
          'I': 'integer', 
          'S': 'semi-continuous', 
          'N': 'semi-integer'}

var_index = ['single', 'daily', 'annual', 'meta_data']

today = datetime.now().strftime("%Y-%m-%d")

###############################################################################
### Main methods
###############################################################################


def make_path(objective=None, Limit=None, make=True, Pareto=False, run_nbr=0):
    """ Creates and return a path to a new result folder according to the model
    objective. 
    """

    if Pareto:         
        # Todays date
        cd = os.path.join('results', '{}'.format(today))
        os.makedirs(os.path.dirname(os.path.join(cd, '')), exist_ok=True)
        # List of files present in the current result dirrectory
        cd = os.path.join('results', f'{today}', f'Pareto_{run_nbr}')
        os.makedirs(os.path.dirname(os.path.join(cd, '')), exist_ok=True)
        
        n = len([f for f in sorted(os.listdir(cd))]) + 1
        name_str = 'Pareto_{}_Objective_{}_CO2Limit_{}'
        result_name = name_str.format(n, objective, None)
        if Limit:
            name_str = 'Pareto_{}_Objective_{}_CO2Limit_{:.5f}'
            result_name = name_str.format(n, objective, Limit)
            
        cd = os.path.join(cd, result_name, '')
        os.makedirs(os.path.dirname(os.path.join(cd, '')), exist_ok=True)
        
    else:
        result_name = 'run_nbr'
        
        # Todays date
        cd = os.path.join('results', '{}'.format(today))
        os.makedirs(os.path.dirname(os.path.join(cd, '')), exist_ok=True)
        # List of files present in the current result dirrectory
        run_nbr = get_last_run_nbr(cd, result_name) + 1
        cd = os.path.join(cd, result_name + '_{}'.format(run_nbr), '')
        
    os.makedirs(os.path.dirname(cd), exist_ok=True)

    return cd


def get_hdf(file_path, *args):
    """ Fetch all items stored in a hdf file and returns a dictionnary. 
        If args are passed only opens the items in args.
    """
    result_dic = {}
    with pd.HDFStore(file_path) as hdf:
        if not args:
            for i in hdf.keys():
                result_dic[i[1:]] = hdf[i]
        elif len(args) > 1:
            for i in args:
                result_dic[i] = hdf[i]
        else:
            result_dic = hdf[args[0]]
    return result_dic


def get_all(m, Threshold, Days, Hours, Periods):
    """ Get all results from the gurobi model m into a dictionnary split in time 
    dependent and
        time independent variables. Get the upper and lower bounds of each variable 
        in a dict.
        Return both dictionnarairies.
    """
    
    def cutoff(r, Threshold):
        """ Cut off all values withing threshold around zero """
        try:
            _ = len(r)
            r[(r > -Threshold) & (r < Threshold)] = 0
        except:
            r = (r if r >= Threshold or r <= -Threshold else 0)
        return r
    
    var_names_cut = set()
    for v in m.getVars():
        name = re.split('\d', v.VarName)[0]
        var_names_cut.add(name)
    
    var_results, var_meta = ({'single': {}, 'daily':{}, 'annual':{}} 
                               for i in range(2))
    get_meta = lambda v: [v.lb, v.ub, vtypes[v.VType]]
    for n in var_names_cut:
        results = []
        
        Time_steps = 'Daily' if 'CGT' not in n else 'Annual'
        if n[-1] == ',' or n[-1] == '[':
            if Time_steps == 'Daily':
                key = 'daily'
                results = get_signle(n, m, Days, Hours, flatten=False)
                meta = get_meta(m.getVarByName(n + '0,0]'))
            elif Time_steps == 'Annual':
                key = 'annual'
                results = get_signle(n, m, Periods)
                meta = get_meta(m.getVarByName(n + '0]'))
            n = n[:-1] + ']' if n[-1] == ',' else n[:-1]
            
        else:
            key = 'single'
            results = m.getVarByName(n).x
            meta = get_meta(m.getVarByName(n))
        
        # Cutoff tiny variable values and negative zero
        cutoff(results, Threshold)
        var_meta[key][n] = meta
        var_results[key][n] = results
    return var_results, var_meta


def save_df_to_hdf5(var_results, var_meta, path, Days, Hours, Periods):
    # Format results into pandas series and dataframe objects
    columns = ['Var_name', 'Value']
    var_results_df = {}
    
    vi = var_index[0]
    var_results_df[vi] = pd.DataFrame(var_results[vi].items(), columns=columns)
    
    vi = var_index[1]
    index_names = ['Var_name', 'Days', 'Hours']
    K = list(var_results[vi].keys())
    index = pd.MultiIndex.from_product([K, Days, Hours], names=index_names)
    var_results_df[vi] = make_df(index, var_results[vi])
    
    vi = var_index[2]
    index_names = ['Var_name', 'Periods']
    K = list(var_results[vi].keys())
    index = pd.MultiIndex.from_product([K, Periods], names=index_names)
    var_results_df[vi] = make_df(index, var_results[vi])
    
    vi = var_index[3]
    index_names = ['Var_index', 'Var_name', 'Bounds']
    K, meta = [], []
    for i in var_index[:-1]:
        K.extend(list(var_meta[i].keys()))
        meta.extend(np.array(list(var_meta[i].values())))
    meta = np.array(meta)
    lb, ub, vtype = meta[:,0], meta[:,1], meta[:,2]
    dic = dict(zip(K, np.zeros(len(K))))
    var_results_df[vi] = pd.DataFrame.from_dict(dic.items())
    var_results_df[vi][1] = lb
    var_results_df[vi]['Upper_bound'] = ub
    var_results_df[vi]['Var_type'] = vtype
    var_results_df[vi].rename(columns={0:'Var_name', 1: 'Lower_bound'}, 
                              inplace=True)
    
    result_dir, file_name = get_directory(path)
    for vi in var_index:    
        with pd.HDFStore(path) as hdf:
            hdf.put(vi, var_results_df[vi], format='table', data_columns=True)
    print(f'All results where saved to {file_name} in {result_dir}')


def save_txt(m, path_dir):
    """ Save large variables to a txt file to help identify bound errors. 
        Save all variables to a txt file to help identify write errors. 
    """
    file_name = 'vars_above_10k.txt'
    with open(os.path.join(path_dir, file_name), 'w') as f:
        for v in m.getVars():
            if v.x > 10000:
                print(v.varName + ': {:.2f}\n'.format(v.x), file=f)
    
    file_name = 'vars_above_10k.txt'
    with open(os.path.join(path_dir, file_name), 'w') as f:
        for v in m.getVars():
                print(v.varName + ': {:.2f}\n'.format(v.x), file=f)

                    
def summary(result_path, save=True):
    """ Given path of the result file creates and returns a summary of results.
        Results are divided into time depenent and time independent results.
        Both dataframes are printed and saved as excel files if specified.
    """    
    var_results_df = get_hdf(result_path)

    # Summary dataframe of single value variables       
    df1 = var_results_df['single']
    
    for b in list(var_results_df['meta_data'].columns)[1:]:
        df1[b] = var_results_df['meta_data'][b][0:len(df1)]
        
    df1 = add_categories(df1)
    
    # Summary dataframe of multiple value variables  
    def get_df_index(df, index_name):
        """ Returns a set of pd Series indexes for a given index name """
        return set(df.index.get_level_values(index_name))
   
    name_set = set()
    for vi in var_index[1:-1]:
        name_set.update(get_df_index(var_results_df[vi], 'Var_name'))
        
    df2 = var_results_df['meta_data'].set_index('Var_name')    
    df2.drop(set(df2.index) - name_set, inplace=True)
    
    val = {}
    values = ['Max', 'Min', 'Mean', 'Shape']
    for v in values:
        val[v] = ['a']*len(name_set)
    
    for i, v in enumerate(values):
        df2.insert(i, v, val[v])
        
    for vi in var_index[1:-1]:
        n_set = get_df_index(var_results_df[vi], 'Var_name')
        for n in n_set:
            value = var_results_df[vi][n].values
            value[value == -0] = 0
            df2.loc[n, 'Max'] = '{:.4f}'.format(np.max(value))
            df2.loc[n, 'Min'] = '{:.4f}'.format(np.min(value) + 1e-10)
            df2.loc[n, 'Mean'] = '{:.4f}'.format(np.mean(value) + 1e-10)
            try:
                df2.loc[n, 'Shape'] = str(var_results_df[vi][n].index.levshape)
            except:
                df2.loc[n, 'Shape'] = str(np.shape(value))
    
    df2.reset_index(inplace=True)
    df2 = add_categories(df2)
    
    # Display and save results
    print('---------------- Time independent Results ----------------')
    print(df1)
    print('\n')
    print('---------------- Time dependent Results ----------------')
    print(df2)
    
    
    if save:
        result_dir, _ = get_directory(result_path)
        file_name = 'time_independent_variables.xlsx'
        df1.to_excel(os.path.join(result_dir, file_name))
        print(f'Result summary saved to {file_name} in {result_dir}')
        file_name = 'time_dependent_variables.xlsx'
        df2.to_excel(os.path.join(result_dir, file_name))
        print(f'Result summary saved to {file_name} in {result_dir}')
    

###############################################################################
### Secondairy methods
###############################################################################


def get_directory(path):
    """ For a given path, returns the directory path and filename """
    path_separator = os.path.join('a','a').split('a')[1]
    file_name = path.split(path_separator)[-1]
    file_dir = os.path.join(*path.split(path_separator)[:-1])
    return file_dir, file_name


def get_signle(var_name, m, *args, flatten=False):
    """ Return an array of result values for a given variable cut name and
        time period either: (Days, Hours) or Periods    
    """
    if len(args) == 2:
        Days, Hours = args
        array = np.zeros((len(Days), len(Hours)))
        for d in Days:
            for h in Hours:
                    array[d,h] = m.getVarByName(var_name + f'{d},{h}]').x
        if flatten:
            array = array.flatten()
        
    elif len(args) == 1:
        Periods = args[0]
        array = np.zeros(len(Periods))
        for p in Periods:
            array[p] = m.getVarByName(var_name + f'{p}]').x
        
    return array


def make_df(index, var_results):
    """ Creates and returns a multindex pandas series object. """
    serie = np.zeros(len(index))
    for i, k in enumerate(list(var_results.keys())):
        var = var_results[k].flatten()
        serie[i*len(var):(i+1)*len(var)] = var
    return pd.Series(serie, index=index)


def get_last_run_nbr(cd, name):
    """ Return the last run number in a given directory. """
    files, runs = [], []
    files = [f for f in sorted(os.listdir(cd))]
    # Increment file name by numbers of run in a day
    for f in files:
        if name in f:
            runs.append(f)
    if not runs:
        run_nbr = 0
    else:
        run_nbr = max([int(i.split('_')[-1]) for i in runs])
        
    return run_nbr


def add_categories(df):
    """ Adds categories and subcategories to organize the different variables
        according to their names.
        Sort first by category then by name.
        Return the modified dataframe.
    """
    cat, subcat = [], []
    for n in df['Var_name']:
        splited = n.split('_')
        if 'unit' in n or 'grid' in n:
            try:
                cat.append(splited[0])
            except:
                cat.append('None')
            try:
                subcat.append(splited[1].split('[')[0])
            except:
                subcat.append('None')
        else:
            cat.append('special')
            if 'T' in n:
                subcat.append('T')
            else:
                try:
                    subcat.append(n.split('[')[0])
                except:
                    subcat.append('None')
    
    df['Category'] = cat    
    df['Subcategory'] = subcat
    df.set_index(['Category', 'Subcategory'], inplace=True)

    df = df.sort_values('Var_name').sort_index()        

    return df


###############################################################################
### END - unused methods
###############################################################################


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
        dic[v] = [np.min(value), np.mean(value), np.max(value), np.shape(value)]
        dic[v] += var_bounds[v]
        if v in V_meta.keys():
            dic[v] += V_meta[v]
    columns = ['Minimum', 'Average', 'Maximum', 'Shape'] + V_meta['Header'][2:]
    df = pd.DataFrame.from_dict(dic, orient='index')
    df.transpose()
    df.columns = columns
    
    return df


def parameters(P, P_meta):
    """ Converts the parameter holder P into a dataframe containing parameter 
    value and metadata
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