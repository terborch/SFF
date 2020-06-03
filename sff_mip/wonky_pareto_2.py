import pandas as pd
import os
from matplotlib import pyplot as plt
import numpy as np

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

def get_pareto_nbr(file_name):
    if 'opex' in file_name:
        return len(list_of_files)
    elif 'capex_Limit_None' in file_name:
        return 1
    else:
        return int(file_name.split('_')[0]) - 1

date = '2020-06-03'
file = 'results.h5' 
Pareto_opex, Pareto_capex = [], []
path = os.path.join('results', date, 'Pareto_3')
list_of_files = [f for f in os.listdir(path)]
Pareto_opex = np.zeros(len(list_of_files))
Pareto_capex = np.zeros(len(list_of_files))
for file_name in list_of_files:
    run_nbr = get_pareto_nbr(file_name)
    print('\n ------------------------------------------------- \n')
    df = get_hdf(os.path.join(path, file_name, file), 'single')
    df.set_index('Var_name', inplace=True)
    opex, capex = float(df.loc['opex']), float(df.loc['capex'])
    Pareto_opex[run_nbr-1] = opex
    Pareto_capex[run_nbr-1] = capex
    print(f'run_{run_nbr}    ', 'opex: {0:.4f} [MCHF/year]    '.format(opex), 
          'capex: {0:.5g} [MCHF/year]'.format(capex))
    
    
plt.title('Pareto possibility frontiere')
plt.xlabel('opex in [MCHF/year]')
plt.ylabel('capex in [MCHF/year]')
plt.ylim(min(Pareto_capex)*0.95, max(Pareto_capex)*1.05)

for file_name in (list_of_files):
    i = get_pareto_nbr(file_name)
    plt.text(Pareto_opex[i - 1], Pareto_capex[i - 1], f'{i}')
    
plt.scatter(Pareto_opex, Pareto_capex, label='capex', marker='o')

path = os.path.join('results', date, 'pareto.png')
plt.savefig(path)

