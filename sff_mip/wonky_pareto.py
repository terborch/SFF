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
    if 'totex' in file_name:
        return len(list_of_files)
    elif 'emissions_CO2Limit_None' in file_name:
        return 1
    else:
        return int(file_name.split('_')[1]) - 1

date = '2020-05-29'
file = 'results.h5' 
Pareto_totex, Perto_emissions = [], []
path = os.path.join('results', date, 'Pareto_2')
list_of_files = [f for f in os.listdir(path)]
Pareto_totex = np.zeros(len(list_of_files))
Perto_emissions = np.zeros(len(list_of_files))
for file_name in list_of_files:
    run_nbr = get_pareto_nbr(file_name)
    print('\n ------------------------------------------------- \n')
    df = get_hdf(os.path.join(path, file_name, file), 'single')
    df.set_index('Var_name', inplace=True)
    totex, emissions = float(df.loc['totex']), float(df.loc['emissions'])
    Pareto_totex[run_nbr-1] = totex
    Perto_emissions[run_nbr-1] = emissions
    print(f'run_{run_nbr}    ', 'TOTEX: {0:.4f} [MCHF]    '.format(totex), 
          'emissions: {0:.5g} [t-CO2]'.format(emissions))
    
    
plt.title('Pareto possibility frontiere')
plt.xlabel('TOTEX in [MCHF/year]')
plt.ylabel('emissions in [t-CO2/year]')
plt.ylim(min(Perto_emissions)*0.95, max(Perto_emissions)*1.05)

for file_name in (list_of_files):
    i = get_pareto_nbr(file_name)
    plt.text(Pareto_totex[i - 1] + 0.03, Perto_emissions[i - 1] + 0.1, f'{i}')
    
plt.scatter(Pareto_totex, Perto_emissions, label='emissions', marker='o')

path = os.path.join('results', date, 'pareto.png')
plt.savefig(path)

