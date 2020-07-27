""" Plot graphs of results present in result dicts
    #   all_dic returns two dicts of time depnent or indepenent variable values 
    #   var_time_indep_summary returns a dataframe summarising time indep results
    #   TODO: add V_meta to time dep df
    #   TODO: add lower and upper bound the time dep df
"""

# External modules
from matplotlib import pyplot as plt
import numpy as np
import os.path
# Internal modules
from read_inputs import (Periods, dt_end, Days, Hours, Ext_T, Irradiance, 
                         Build_cons, Build_T, AD_T, Fueling, Frequence)
from global_set import (Units, Units_storage, Resources, Color_code, 
                        Linestyle_code, Linestyles, Abbrev)
import results
from data import get_hdf

###############################################################################
### Global variables to be eliminated
###############################################################################

# Plot settings
fig_width, fig_height = 11.7*2, 5.8

# Converting hourly to daily values
# Day_Dates = []
# Days = (Dates[-1] - Dates[0]).days
# Last_day_hours = int((Dates[-1] - Dates[0]).seconds/3600)
# Days += 1 if Last_day_hours >= 0 else 0
# Day_Dates = [Dates[i*24] for i in range(Days)]
# Day_Dates.append(dt_end)

###############################################################################
### Primary methods
###############################################################################
def plot_value(axis, x_position, value):
    if np.round(value) > 0:
        ysize = axis.get_ylim()[1] - axis.get_ylim()[0]
        axis.text(x_position, value + ysize*0.05, '{:.0f}'.format(value))

def unit_size(path):
    """ Plot a bar chart of the installed capacity of each unit given a path to
        the hdf result file.
    """
    # Split into torage and non storage units
    Names, Values = {}, {}
    Units_ns = list(set(Units) - set(Units_storage))
    Units_ns.sort()
    Names['non_storage'] = [f'unit_size[{u}]' for u in Units_ns]
    Names['storage'] = [f'unit_size[{u}]' for u in Units_storage]
     
    # Only time independent results are used, set names as index
    df = get_hdf(path, 'single')
    df.set_index('Var_name', inplace=True)
    for t in ['non_storage', 'storage']:
        Values[t] = [df.loc[n, 'Value'] for n in Names[t]]   

    # Figure options
    fig, ax1 = plt.subplots()
    plt.title('Installed capacity for each unit')
    fig.set_size_inches(8, 3)
    ax2 = ax1.twinx()
    ax1.set_ylabel('Production capacity in kW')
    ax2.set_ylabel('Storage capacity in kWh')
    ax1.set_xlim(-1, len(Units))
    ax1.set_ylim(0, max(Values['non_storage'])*1.25)
    ax2.set_ylim(0, max(Values['storage'])*1.25)
    
    i = 0
    for n in Names['non_storage']:
        ax1.bar(i, df.loc[n, 'Value'], color='darkgrey')
        plot_value(ax1, i - 0.25, df.loc[n, 'Value'])
        i += 1
    for n in Names['storage']:
        ax2.bar(i, df.loc[n, 'Value'], color='lightgrey')
        plot_value(ax2, i - 0.25, df.loc[n, 'Value'])
        i += 1
                
    # Store the figure in aplt object accessible anywhere
    Names_order = Units_ns + list(Units_storage)
    plt.xticks(range(len(Units)), 
               [Abbrev[Names_order[i]] for i in range(len(Units))])
    fig.autofmt_xdate()
    plt.tight_layout()


def all_results(Per_cent_vary, path):
    """ Plot all time dependent results that vary more than 1%
        # TODO option to plot daily averages only
    """
    
    # Get relevant results into dic
    df = get_hdf(path, 'daily')
    Time_steps = list(range(len(Hours)*len(Days)))
    
    # Get the names of variables that vary more than 1%
    var_name_vary = []
    for n in set(df.index.get_level_values(0)):
        if df[n].max() > Per_cent_vary*df[n].min():
            var_name_vary.append(n)
    var_name_vary.sort()
    
    # Plot each variables and stack them vertically
    fig, axs = plt.subplots(len(var_name_vary), 1, sharex=True)
    fig.set_size_inches(20, 50)
    plt.xlabel('Day')
    fig.subplots_adjust(hspace=0)
    i = 0
    for n in var_name_vary:
        axs[i].plot(Time_steps, df[n], label=n, c=col(n))
        axs[i].legend(loc='upper right')
        axs[i].set_ylabel(get_resource_name(n))
        set_x_ticks(axs[i], Time_steps)
        i += 1
        
    # if daily:
    #     Dates = Day_Dates
    #     var_result = hourly_to_daily_list(var_result, var_name)
        
        
def resource(Resource, Threshold, path):
    
    # Get relevant results into dic
    df = get_hdf(path, 'daily')
    Time_steps = list(range(len(Hours)*len(Days)))
    
    names = []
    for n in set(df.index.get_level_values(0)):
        if Resource in n:
            if df[n].max() >= Threshold or df[n].min() <= -Threshold:
                names.append(n)
    
    nbr_fig = len(names) + 1 if Resource == 'Elec' else len(names)
    
    fig, axs = plt.subplots(nbr_fig, 1, sharex=True)
    fig.set_size_inches(fig_width, fig_height*nbr_fig)
    plt.xlabel('Date')
    fig.subplots_adjust(hspace=0)
    i = 0
    for n in names:
        axs[i].plot(Time_steps, df[n], label=n, c=col(n), ls=ls(n))
        axs[i].legend(loc='upper right')
        axs[i].set_ylabel(get_resource_name(n) + ' in kW')
        i += 1        
    
    if Resource == 'Elec':
        axs[i].plot(Time_steps, np.repeat(Build_cons['Elec'], len(Days)),
                    label='Building consumption', 
                    c=col('Elec'), ls=ls('build'))
        axs[i].legend(loc='upper right')
        axs[i].set_ylabel(get_resource_name(n) + ' in kW')
        
        
    # if daily:
    #     Dates = Day_Dates
    #     var_result = hourly_to_daily_list(var_result, var_name)
    #     Build_cons = hourly_to_daily(Build_cons_Elec)
    # else:
    #     Build_cons = Build_cons_Elec        
    
    
def PV_results(path):
    """ Plot the electricity production of the PV panels agains irradiance 
        # TODO option to plot daily averages only
    """
    
    # Get relevant results into dic
    df = get_hdf(path, 'daily')
    Time_steps = list(range(len(Hours)*len(Days)))
    
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title('PV results')
    ax1.set_xlabel('Dates')
    ax1.set_ylabel('Global Irradiance in kW/m^2')
    set_x_ticks(ax1, Time_steps)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Electricity produced in kW')
    
    n = 'Irradiance'
    ax1.plot(Time_steps, Irradiance.flatten(), label=n, color=col(n))
    n = 'unit_prod[PV][Elec]'
    ax2.plot(Time_steps, df[n].values, label=n, color=col(n), ls=ls(n))

    ax1.legend(loc='center left') 
    ax2.legend(loc='center right')
    
    
    # if daily:
    #     Dates = Day_Dates
    #     Irr = hourly_to_daily(Irradiance)
    #     n = 'unit_prod[PV][Elec]'
    #     var_result[n] = hourly_to_daily(var_result[n])
    # else:
    #     Irr = Irradiance
    
    
def SOFC_results(path):
    """ Plot all variables results relative to  the SOFC """
    # Get relevant results into dic
    df = get_hdf(path, 'daily')
    Time_steps = list(range(len(Hours)*len(Days)))
    
    # Items to plot
    items = {}
    items['name'] = ['unit_prod[SOFC][Elec]', 'unit_cons[SOFC][Gas]', 
                     'unit_cons[SOFC][Biogas]', 'unit_prod[SOFC][Heat]']
    items['label'] = [unit_labels(n) for n in items['name']]
    
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title('SOFC')
    ax1.set_xlabel('Dates')
    ax1.set_ylabel('Resources consumed and produced by the SOFC in kW')
    set_x_ticks(ax1, Time_steps)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Heat produced by the SOFC in kW')
    
    for i, n in enumerate(items['name'][:-1]):
        ax1.plot(Time_steps, df[n], label=items['label'][i], 
                 color=col(n), ls=ls(n)) 
    n = 'unit_prod[SOFC][Heat]'
    ax2.plot(Time_steps, df[n], label=items['label'][-1], 
             color=col(n), ls=ls(n))

    ax1.legend(loc='upper left') 
    ax2.legend(loc='upper right')
    
    
def SOC_results(path):
    """ Plot all variables results relative to  the SOFC """
    
    def set_x_ticks(ax1, Time_steps):
        day_tics = [f'Day {d+1}' for d in range(0,365)]
        ax1.set_xticks(Time_steps[12::24], minor=False)
        ax1.set_xticklabels(day_tics, fontdict=None, minor=False) 
    
    # Get relevant results into dic
    soc = get_hdf(path, 'annual')
    df = get_hdf(path, 'single').set_index('Var_name')['Value']
    Time_steps = list(range(len(Hours)*365))
    
    if max(df[f'unit_size[{n}]'] for n in ['BAT', 'CGT']) <= 0:
        return
    
    # Items to plot
    items = {}
    items['name'] = ['BAT', 'CGT']
    items['label'] = ['Battery SOC', 'Compressed Gas Tank SOC']
    items['resource'] = ['Elec', 'Biogas']
    
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width*10, fig_height)
    plt.title('Storage Normalized State of Charge (SOC)')
    ax1.set_xlabel('Dates')
    ax1.set_ylabel('State of Charge [-]')
    set_x_ticks(ax1, Time_steps)
    
    # Convert the SOC result in kW to percent relative to max capacity
    for i, n in enumerate(items['name']):
        ax1.plot(soc[f'unit_SOC[{n}]']/df[f'unit_size[{n}]'], 
                 label=items['label'][i], color=col(items['resource'][i]), ls=ls(n)) 
    ax1.legend(loc='upper left')
    fig.autofmt_xdate()
    plt.tight_layout()

    

def all_fig(path, save_fig=True):
    
    cd, _ = results.get_directory(path)
    
    unit_size(path)
    print_fig(save_fig, os.path.join(cd, 'installed_capacity.png'))
        
    # unit_temperature(path)
    # print_fig(save_fig, os.path.join(cd, 'temperature_results.png'))
    
    Per_cent_vary = 1.01
    all_results(Per_cent_vary, path)
    print_fig(save_fig, os.path.join(cd, 'all_results.png'))
    
    Threshold = 1e-6
    for r in ['Elec', 'Gas', 'Biogas']:
        resource(r, Threshold, path)
        print_fig(save_fig, os.path.join(cd, f'resource_{r}.png'))
    
    PV_results(path)
    print_fig(save_fig, os.path.join(cd, 'PV.png'))  
        
    SOFC_results(path)
    print_fig(save_fig, os.path.join(cd, 'SOFC.png'))
    
    #flows('v[', 'water flows', 'm^3/h', var_result_time_dep, var_name_time_dep, sort=True, daily=True)
    #print_fig(save_fig, os.path.join(cd, 'Hot_water_flows.png'))
    
    #flows('Heat', 'heat flows', 'kW', var_result_time_dep, var_name_time_dep, sort=True, daily=True)
    #print_fig(save_fig, os.path.join(cd, 'Heat_flows.png'))


def pareto(*args, date=None, print_it=False, Xaxis='totex', Yaxis='emissions'):
    if args:
        path = args[0]
    else:
        cd = os.path.join('results', date)
        nbr = results.get_last_run_nbr(cd, 'Pareto')
        path = os.path.join(cd, f'Pareto_{nbr}')
        
        # if 'pareto.png' in [f for f in sorted(os.listdir(path))]:
        #     print('Pareto figures already in pareto result folder')
        #     return
    
    def get_pareto_nbr(file_name):
        return int(file_name.split('_')[0])
    
    ### Pareto scatter plot
    Pareto = []
    list_of_files = [f for f in os.listdir(path)]
    for file_name in list_of_files:
        file_path = os.path.join(path, file_name, 'results.h5')
        df = get_hdf(file_path, 'single')
        df.set_index('Var_name', inplace=True)
        X, Y = float(df.loc[Xaxis]), float(df.loc[Yaxis])
        Pareto.append([file_name, X, Y])
        
    # Sort the Pareto list along Xaxis
    Pareto.sort(key=lambda x: x[1])
    X = [sublist[1] for sublist in Pareto]
    Y = [sublist[2] for sublist in Pareto]
    unit = {'totex': '[MCHF/year]',
            'opex': '[MCHF/year]',
            'capex': '[MCHF/year]',
            'emissions': '[kt-CO2/year]'}
    
    # Plot options
    plt.title('Pareto possibility frontiere')
    plt.xlabel(f'{Xaxis} in ' + str(unit[Xaxis]))
    plt.ylabel(f'{Yaxis} in ' + str(unit[Yaxis]))
    plt.ylim(min(Y)*0.95, max(Y)*1.05)
    
    # Plot pareto point number
    for i, _ in enumerate(X):
        # Text on graph
        plt.text(X[i] + 0.0015, Y[i] + 0.0015, f'{i + 1}')
        
        # Rename directories according to the pareto points
        l = Pareto[i][0].split('_')
        l[0] = f'{i+1}'
        name = '_'.join(l)
        cd_old = os.path.join(path, Pareto[i][0])
        cd_new = os.path.join(path, name)
        os.rename(cd_old, cd_new)
    
    # Grab the list of files with new names and deduce next graph size
    list_of_files = [f for f in os.listdir(path)]
    
    # Pareto scatter plot
    plt.scatter(X, Y, marker='o')
    
    # Save figure
    fig_path = os.path.join(path, 'pareto.png')
    plt.savefig(fig_path)
    
    ### Pareto units installed
    n_pareto = len(list_of_files)
    fig, ax1 = plt.subplots(n_pareto, 1, sharex=True)
    fig.set_size_inches(8, 2*n_pareto)
    fig.subplots_adjust(hspace=0)
    ax2 = np.array(range(n_pareto), dtype=object)

    # Split into storage and non storage units
    Names, Values = {}, {}
    Units_ns = list(set(Units) - set(Units_storage))
    Units_ns.sort()
    Names['non_storage'] = [f'unit_size[{u}]' for u in Units_ns]
    Names['storage'] = [f'unit_size[{u}]' for u in Units_storage]
        
    for file_name in list_of_files:
        p = get_pareto_nbr(file_name) - 1
        file_path = os.path.join(path, file_name, 'results.h5')
        
        # Only time independent results are used, set names as index
        df = get_hdf(file_path, 'single')
        df.set_index('Var_name', inplace=True)
        for t in ['non_storage', 'storage']:
            Values[t] = [df.loc[n, 'Value'] for n in Names[t]]   
    
        # Figure options
        ax2[p] = ax1[p].twinx()
        ax1[p].set_ylabel(f'{p + 1} \n Capacity in kW')
        ax2[p].set_ylabel(f'Capacity in kWh \n {p + 1}')
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
    
    fig_path = os.path.join(path, 'units.png')
    plt.savefig(fig_path)
    
    
   
def inputs():
    """ Represent all inputs in a few graphs.
        1. Frequency, Temperature and Irradiance are presented once at top
        2. Unit temperatures
        3. Heat consumption
        4. Fuel Consumption
    """
    
    def frequency(ax):
        # Frequency in background
        ax3 = ax.twinx()
        ax3.spines['top'].set_visible(False)
        ax3.axis('off')
        ax3.bar(Time_steps[int(len(Hours)/2)::len(Hours)], Frequence.T[0], 
                alpha=0.15, width=23, color='grey', label='Freuqnecy')
        return ax3
    
    def temperature(ax):
        ax2 = ax.twinx()
        ax2.spines['top'].set_visible(False)
        ax2.set_ylabel('Temperature in °C')
        ax2.step(Time_steps, Ext_T.flatten(), label='Exterior Temperature', 
             color='blue')    
        return ax2
    
    Time_steps = list(range(len(Hours)*len(Days)))
    fig_width, fig_height = 11.7*2, 5.8
    
    """ Weather and Frequency """
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    set_x_ticks(ax1, Time_steps)
    ax2 = ax1.twinx()
    
    ax1.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    
    plt.title('Weather and Frequency of each of typical day')
    ax1.set_xlabel('Clustered Days')
    ax1.set_ylabel('Temperature in °C')
    ax2.set_ylabel('Global Irradiance in kW/m^2')
    
    ax3 = frequency(ax1)
    position = [f + 1 for f in Frequence.T[0]]
    position[2:-2] = [f/2 for f in Frequence.T[0][2:-2]]
    for i, f in enumerate(Frequence.T[0]):
        ax3.text(Time_steps[int(len(Hours)/2)::len(Hours)][i], position[i],
                 int(f), horizontalalignment='center')
    
    ax1.step(Time_steps, Ext_T.flatten(), label='Exterior Temperature', 
             color='blue')    
    ax2.step(Time_steps, Irradiance.flatten(), label='Irradiance', color='red')
    ax1.legend(loc='upper left') 
    ax2.legend(loc='upper right')
    ax3.legend(loc='upper center')
    
    def reduce(ax, percent):
        ax.set_ylim(ax.get_ylim()[0], ax.get_ylim()[1]*percent)
    reduce(ax1, 1.2)
    reduce(ax2, 1.2)
    reduce(ax3, 1.1)

    
    
    """ Unit Temperatures """
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    set_x_ticks(ax1, Time_steps)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    plt.title('Weather and Frequency of each of typical day')
    ax1.set_xlabel('Clustered Days')
    ax1.set_ylabel('Temperature in °C')
    ax3 = frequency(ax1)
    
    ax1.step(Time_steps, Ext_T.flatten(), label='Exterior Temperature', 
             color='blue')  
    ax1.scatter(Time_steps, Build_T.flatten(), label='Building Tempreature', 
              color='black', s = 5)
    ax1.scatter(Time_steps, AD_T.flatten(), label='AD Temperature', 
              color='green', s = 5)
    
    ax1.legend()
    
    
    
    
    """ Electric Consumption in a day """
    Profile = Build_cons['Elec'].T[0]
    fig, ax1 = plt.subplots()
    ax1.spines['right'].set_visible(False)
    ax1.spines['top'].set_visible(False)
    plt.step(Hours, Profile, where='post', c='blue')
    plt.title('Instant Electric Consumption')
    plt.ylabel('Electric Consumption in kW')
    plt.xlabel('Time of the day in Hours')       
    plt.xticks(Hours[::2])
    plt.ylim(0,250)
    plt.show()



    """ Heat Consumption in a year """
    def set_x_ticks(ax1, Time_steps):
        day_tics = [f'Day {d+1}' for d in Days]
        ax1.set_xticks(Time_steps[12::24], minor=False)
        ax1.set_xticklabels(day_tics, fontdict=None, minor=False)  
    
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title('Heat Consumption')
    ax1.spines['top'].set_visible(False)
    
    ax1.set_xlabel('Clustered Days')
    ax1.set_ylabel('Building Heat consumption in kW')
    set_x_ticks(ax1, Time_steps)
    
    # Frequency in background
    ax3 = frequency(ax1)
    ax2 = temperature(ax1)
    n = 'Building Heat Consumption'
    ax1.step(Time_steps, Build_cons['Heat'].flatten(), label=n, c='red')
    # n = 'AD Heat Consumption'
    # ax2.step(Time_steps, AD_cons_Heat.flatten(), label=n, c='green')
    
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.show()
    
    
    """ Fuel consumption """
    title = 'Fuel Consumption'
    fig, ax1 = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title(title)
    ax1.spines['top'].set_visible(False)
    ax1.set_xlabel('Clustered Days')
    ax1.set_ylabel('Fuel consumption in kW')
    set_x_ticks(ax1, Time_steps)
    ax2 = temperature(ax1)
    ax3 = frequency(ax1)
    n = 'Fuel Consumption'
    ax1.step(Time_steps, Fueling.flatten(), label=n, c='black')
    
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.show()
    
    
def clustering(Number_of_clusters):
    
    # A list of dates in day/month format
    D = 365
    import pandas as pd
    from datetime import datetime
    datelist = pd.date_range(datetime.strptime('2019-01-01', '%Y-%m-%d'), periods=D).tolist()
    D_list, M_list = [0]*D, [0]*D
    for d in range(D):
        D_list[d] = f'{datelist[d].day}/{datelist[d].month}'
        M_list[d] = f'{datelist[d].strftime("%b")}'
    
    
    import data
    Days = range(D)
    path = os.path.join('inputs', 'clusters.h5')
    Clusters = get_hdf(path, Series=True)
    n = f'Cluster_{Number_of_clusters}'
    Clusters[n] = list(Clusters[n].astype(int))
    Labels, Closest = Clusters[n][:D], Clusters[n][D:]
    Clusters_order = data.arrange_clusters(Labels)
    Clustered_days = data.reorder(Closest, Clusters_order)
    Frequence = data.get_frequence(Labels)
    Frequence = data.reorder(Frequence, Clusters_order)
    
    
    S, _ = data.get_param('settings.csv')
    filename = 'meteo_Liebensberg_10min.csv'
    epsilon = 1e-6
    Ext_T, Irr, _ = data.weather_param(filename, epsilon, 
                                       (Days, Hours), S['Time'])
    
    Ext_T_cls = data.cluster(Ext_T, Clustered_days, Hours)
    Irr_cls = data.cluster(Irr, Clustered_days, Hours)

    def repeat(Values, Frequence):
        """ Return a liste of repeated values by frequencies """
        List = []
        for i, f in enumerate(Frequence):
            List.append([Values[i]]*int(f))
        List = [item for sublist in List for item in sublist]
        return List
    
    Ext_T_cls = repeat(np.mean(Ext_T_cls, axis=1), Frequence)
    Irr_cls = repeat(np.mean(Irr_cls, axis=1), Frequence)
     
    def set_axis():
        """ Set xlabel to 'Date'
            Set xticks as months    
            Remove splines
            Add legend and autoformat layout
        """
        ax.set_xlabel('Date')
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        plt.xticks(Days[::31], M_list[::31])
        plt.legend()
        fig.tight_layout()
        fig.autofmt_xdate()
        
        
    fig, ax = plt.subplots()
    plt.title('Clustering results - Irradiance')
    c = 'red'
    ax.set_ylabel('Daily average Irradiance in kW/m^2')
    ax.plot(Days, np.mean(Irr, axis=1), c=c, alpha=0.3, label='Measured')
    ax.step(Days, Irr_cls, where='post', c=c, label='Clustered')   
    set_axis()
    plt.show()
    
    fig, ax = plt.subplots()
    plt.title('Clustering results - Temperature')
    c = 'blue'
    ax.set_ylabel('Daily average Temperature in °C')
    ax.plot(Days, np.mean(Ext_T, axis=1), c=c, alpha=0.3, label='Measured')
    ax.step(Days, Ext_T_cls, where='post', c=c, label='Clustered')
  
    set_axis()
    plt.show()

    
###############################################################################
### Secondairy methods
###############################################################################


def get_resource_name(var_name):
    """ Get the abbreviated name of a resoucre from a variable name string """
    name = []
    for r in Resources:
        if r in var_name:
            name.append(r)
    if not name:
        name.append('default')
    return(name[0])
        
def get_unit_name(var_name):
    """ Get the abbreviated name of a unit from a variable name string """
    name = []
    for u in Units:
        if f'[{u}]' in var_name:
            name.append(u)
    if not name:
        name.append('default')
    return(name[0])

def col(var_name):
    """ Return the color code of a corresponding resource """
    r = get_resource_name(var_name)
    return Color_code[r]

def ls(var_name):
    """ Return the linestyle code of a corresponding unit """
    u = get_unit_name(var_name)
    if Linestyle_code[u] in Linestyles.keys():
        return Linestyles[Linestyle_code[u]]
    else:
        return Linestyle_code[u]

def print_fig(save_fig, cd):
    """ Either display or save the figure to the specified path, then close the figure. """
    if save_fig:
        try:
            plt.savefig(cd)
            print(f'Figure saved at {cd}')
        except:
            print(f'Empty figure could not be saved at {cd}')
    else:
        plt.show()
    plt.clf()
    

def set_x_ticks(ax1, Time_steps):
    day_tics = [f'Day {d+1}' for d in Days]
    ax1.set_xticks(Time_steps[12::24], minor=False)
    ax1.set_xticklabels(day_tics, fontdict=None, minor=False)  
    

def unit_labels(unit_name):
    l = unit_name.split('_')[1].split('[')
    return '{} {} {}'.format(l[1][:-1], l[0], l[2][:-1])


def make_patch_spines_invisible(ax):
    for p in ['top', 'right', 'left']:
        ax.spines[p].set_visible(False)

###############################################################################
### END
###############################################################################


"""
def flows(indicator, name, units, var_result, var_name, sort=False,  daily=True):
        
    fig, ax = plt.subplots()
    fig.set_size_inches(fig_width, fig_height)
    plt.title(name)
    plt.xlabel('Dates')
    plt.ylabel(name + units)
    # Get relevant flows according to indicator
    flows, flows_name = [], []
    for n in var_result:
        if indicator in n:
            flows.append(var_result[n])
            flows_name.append(n)
    # Sort in decreasing order each flow by maximum value
    if sort:
        flows_sort = sort_from_index(flows, sorted_index(flows))
        flows_name_sort = sort_from_index(flows_name, sorted_index(flows))
    else: flows_sort, flows_name_sort = flows,  flows_name
    
    
    for f, n in zip(flows_sort, flows_name_sort):
        plt.plot(Dates, f, ls=ls(n))
    plt.legend(flows_name_sort)
    
    
    # if daily:
    #     Dates = Day_Dates
    #     var_result = hourly_to_daily_list(var_result, var_name)
    

def hourly_to_daily(hourly_values):
    i, j = 0, 24
    daily_average = []
    for d in range(Days):
        daily_average.append(sum(hourly_values[i:j])/24)
        i, j = 24*d, 24*(1 + d)
    daily_average.append(sum(hourly_values[i:-1])/Last_day_hours)
    return daily_average

def hourly_to_daily_list(var_result, var_name):     
    daily_var_result = {}
    for n in var_name:
        daily_var_result[n] = hourly_to_daily(var_result[n])
    return daily_var_result

def normalize(l):
    return [l[i]/max(l) for i in range(len(l))]

def sorted_index(unsorted_list):
    
    new_index = []
    j = 0
    for i in range(0,len(unsorted_list)):
        new_index.append([max(unsorted_list[i]), j])
        j += 1
        
    new_index.sort(reverse = True)
    
    for i in range(0, len(new_index)):
        new_index[i][0] = i
        
    return new_index 

def sort_from_index(unsorted_list, new_index):
    sorted_list = [ [] for i in range(len(new_index)) ]
    for i in new_index:
        sorted_list[i[0]] = unsorted_list[i[1]]
        
    return sorted_list

def transpose_list(l):
    
    return list(map(list, zip(*l)))


"""


""" Returns the transpose of a given list. """
""" Given a list of lists returns an index (lost of pairs) where the first element is 0, 1, 2... n 
        the new index sorted by the largest element in each list in decreasing order. The second element
        is the index of the same list in the original list of list.
"""



"""
def resource(resource, var_result, var_name):
    fig, ax1 = plt.subplots()
    ax1.set_xlabel('Dates')
    ax1.set_ylabel(Abbrev[resource] + ' exchanged with units in kW')
    ax2 = ax1.twinx()
    ax2.set_ylabel(Abbrev[resource] + ' exchanged with grids and buildings in kW')
    ax1.set_xlim(Dates[0], Dates[-1])
    
    for n in var_name:
        if resource in n:
            if 'grid' not in n:
                if 'prod' in n:
                    ax1.plot(Dates, var_result[n], label=n, c=col(n), ls=ls(n))
                else:
                    ax1.plot(Dates, [var_result[n][p]*(-1) for p in Periods], 
                             label=n, c=col(n), ls=ls(n))
            else:
                if 'import' in n:
                    ax2.plot(Dates, var_result[n], label=n, c=col(n), ls=ls(n))
                else:
                    ax2.plot(Dates, [var_result[n][p]*(-1) for p in Periods], 
                             label=n, c=col(n), ls=ls(n))
    
    if resource == 'Elec':
        ax2.plot(Dates, Build_cons_Elec, label = 'Building consumption', c=col('Elec'), ls=ls(n))

    ax1.legend(loc='center left') 
    ax2.legend(loc='center right')
"""   