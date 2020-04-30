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

date = '2020-04-30'
file = 'df_time_indep.csv' 
nbr_pareto = 9
Pareto_totex, Perto_emissions = [], []
for i in range(1, nbr_pareto + 1):
    run_name = f'1_year_min_totex_daily_average_cap_emissions_{i}'
    df = open_csv(file, date, run_name, ',')
    Pareto_totex.append(df['Value']['totex'])
    Perto_emissions.append(df['Value']['emissions'])
    print(f'run_{i}    ', 'TOTEX: {0:.4f} [MCHF]    '.format(df['Value']['totex']), 
          'emissions: {0:.5g} [t-CO2]'.format(df['Value']['emissions']))
    
    
plt.title('Pareto possibility frontiere')
plt.xlabel('TOTEX in [MCHF]')
plt.ylabel('emissions in [t-CO2]')

plt.plot(Pareto_totex, Perto_emissions, label='emissions')
plt.legend()

path = os.path.join('results', date, 'pareto.png')
plt.savefig(path)