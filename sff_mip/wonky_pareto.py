import pandas as pd
import os
from matplotlib import pyplot as plt

def open_csv(file, date, run_name, separator):
    """ Open a csv file in a results subfolder given a file name, a run_name, a date and 
        a separator. 
    """
    path = os.path.join('results', date, run_name, file)
    df = pd.read_csv(path , sep=separator, engine='python')
    
    if df.columns[0][0] == 'ï':
        rename_csv(df)
    
    df.set_index(df['Unnamed: 0'], inplace = True)
        
    return df

date = '2020-05-06'
file = 'df_time_indep.csv' 
Pareto_totex, Perto_emissions = [], []
path = os.path.join('results', date)
list_of_files = [f for f in sorted(os.listdir(path))]
for i, file_name in enumerate(list_of_files):
    run_name = file_name
    df = open_csv(file, date, run_name, ',')
    Pareto_totex.append(df['Value']['totex'])
    Perto_emissions.append(df['Value']['emissions'])
    print(f'run_{i}    ', 'TOTEX: {0:.4f} [MCHF]    '.format(df['Value']['totex']), 
          'emissions: {0:.5g} [t-CO2]'.format(df['Value']['emissions']))
    
    
plt.title('Pareto possibility frontiere')
plt.xlabel('TOTEX in [MCHF/year]')
plt.ylabel('emissions in [t-CO2/year]')
plt.ylim(Perto_emissions[0]*0.95, Perto_emissions[-1]*1.05)

for i, file_name in enumerate(list_of_files):
    plt.text(Pareto_totex[i], Perto_emissions[i] + 5, f'{i + 1}')
    
plt.plot(Pareto_totex, Perto_emissions, label='emissions', marker='o')

path = os.path.join('results', date, 'pareto.png')
plt.savefig(path)

