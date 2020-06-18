import pandas as pd
import os
from matplotlib import pyplot as plt
import numpy as np

from global_set import Units, Units_storage, Abbrev
import results
import plot

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
    elif 'emissions_Limit_None' in file_name:
        return 1
    else:
        return int(file_name.split('_')[0]) - 1

def unit_size(path, n_pareto, n):
    """ Plot a bar chart of the installed capacity of each unit given a path to
        the hdf result file.
    """
    # Only time independent results are used, set names as index
    df_result = results.get_hdf(path, 'single')
    df_result.set_index('Var_name', inplace=True)
    var_names = [f'unit_size[{u}]' for u in Units]   

    # Figure options
    fig, ax1 = plt.subplots(n_pareto, 1, sharex=True)
    plt.title('Installed capacity for each unit')
    fig.set_size_inches(8, 3)
    ax2 = ax1.twinx()
    ax1.set_ylabel('Installed production capacity in kW')
    ax2.set_ylabel('Installed storage capacity in kWh')
    fig.subplots_adjust(hspace=0)
    
    # Split into torage and non storage units
    Units_non_storage = list(set(Units) - set(Units_storage))
    Units_non_storage.sort()
    i = 0
    for n in [f'unit_size[{u}]' for u in Units_non_storage]:
        ax1[n].bar(i, df_result.loc[n, 'Value'], color='darkgrey')
        i += 1
    for n in [f'unit_size[{u}]' for u in Units_storage]:
        ax2[n].bar(i, df_result.loc[n, 'Value'], color='lightgrey')
        i += 1
                
    # Store the figure in aplt object accessible anywhere
    Names_order = Units_non_storage + list(Units_storage)
    plt.xticks(range(len(Units)), [Names_order[i] for i in range(len(Units))])
    
date = '2020-06-10'
file = 'results.h5'
folder =  'Pareto_1'
Pareto_totex, Perto_emissions = [], []
path = os.path.join('results', date, folder)
list_of_files = [f for f in os.listdir(path)]
Pareto_totex = np.zeros(len(list_of_files))
Perto_emissions = np.zeros(len(list_of_files))
for file_name in list_of_files:
    run_nbr = get_pareto_nbr(file_name)
    print('\n ------------------------------------------------- \n')
    file_path = os.path.join(path, file_name, file)
    df = get_hdf(file_path, 'single')
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
plt.plot()
path = os.path.join('results', date, folder, 'pareto.png')
plt.savefig(path)



date = '2020-06-10'
file = 'results.h5'
folder =  'Pareto_1'
Pareto_totex, Perto_emissions = [], []
path = os.path.join('results', date, folder)

n_pareto = len(list_of_files)
fig, ax1 = plt.subplots(n_pareto, 1, sharex=True)
fig.set_size_inches(8, 2*n_pareto)
fig.subplots_adjust(hspace=0)
ax2 = np.array(range(n_pareto), dtype=object)

def plot_value(axis, x_position, value):
    if value > 0:
        ysize = axis.get_ylim()[1] - axis.get_ylim()[0]
        axis.text(x_position, value + ysize*0.05, '{:.0f}'.format(value))

# Split into torage and non storage units
Names, Values = {}, {}
Units_ns = list(set(Units) - set(Units_storage))
Units_ns.sort()
Names['non_storage'] = [f'unit_size[{u}]' for u in Units_ns]
Names['storage'] = [f'unit_size[{u}]' for u in Units_storage]
    
for file_name in list_of_files:
    p = get_pareto_nbr(file_name) - 1
    file_path = os.path.join(path, file_name, file)
    
    # Only time independent results are used, set names as index
    df = results.get_hdf(file_path, 'single')
    df.set_index('Var_name', inplace=True)
    for t in ['non_storage', 'storage']:
        Values[t] = [df.loc[n, 'Value'] for n in Names[t]]   

    # Figure options
    ax2[p] = ax1[p].twinx()
    ax1[p].set_ylabel(f'{p} \n Capacity in kW')
    ax2[p].set_ylabel(f'Capacity in kWh \n {p}')
    ax1[p].set_xlim(-1, len(Units))
    ax1[p].set_ylim(0, max(Values['non_storage'])*1.2)
    ax2[p].set_ylim(0, max(Values['storage'])*1.2)
    
    i = 0
    for n in Names['non_storage']:
        ax1[p].bar(i, df.loc[n, 'Value'], color='darkgrey')
        plot_value(ax1[p], i - 0.25, df.loc[n, 'Value'])
        i += 1
    for n in Names['storage']:
        ax2[p].bar(i, df.loc[n, 'Value'], color='lightgrey')
        plot_value(ax2[p], i - 0.25, df.loc[n, 'Value'])
        i += 1
                
    # Store the figure in aplt object accessible anywhere
    Names_order = Units_ns + list(Units_storage)
    plt.xticks(range(len(Units)), 
               [Abbrev[Names_order[i]] for i in range(len(Units))])

#ax1[0].tick_params(axis="x", bottom=True, top=True, labelbottom=True, labeltop=True)
fig.autofmt_xdate()
fig.tight_layout()
plt.subplots_adjust(hspace=0)


path = os.path.join('results', date, folder, 'units.png')
plt.savefig(path)