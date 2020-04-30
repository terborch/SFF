"""
### Model setup and initialization. Get parameters and settings. Define time related parameters. 
    #   m       the global Gurobi MILP model
    #   P       dict with parameters values from parameters.csv will contain calculated parameters
                P has at least two entries, the first is the Category and the second is the
                parameter name or sub-category. Categories is a list of Category names.
    #   S       dict with settings values from settings.csv
    #   P_meta  dict tracking the metadata of model parameters
    #   S_meta  dict tracking the metadata of model settings
    #   V_meta  dict tracking the metadata of model variables
    #   C_meta  dict tracking the metadata of model constraints
    #   Bound       the upped bound of most variables
    #   Periods     list of time period indexes
    #   Time_steps  the number of timesteps
    #   dt          the duration of a time step in hours
    #   Days        list of days in a date format '2019-01-01'
    #   Time        list of hours in a day in a time format '12:00:00'
    #   make_param  function passing values and metadata of a parameter into P and P_meta
"""

# External modules
import gurobipy as gp
import numpy as np
from datetime import datetime, timedelta
# Internal modules
import data


def print_error(error):
    switcher = { 
        'Time_step' : 'Time_step has to be either a number of hours or a nuber of minutes',
        'Time_step_int' : 'Time_step is not an integer number'
    }
    message = switcher.get(error, 'unspecified error')
    
    print('########################## ERROR ##########################')
    print(message)
    print('########################## ERROR ##########################')
    

def get_values_df(file):
    """ Get data from a csv file and return a datafram. Convert every 'Value' entry into a float
        except for entries in the cathegory 'Time'
    """
    df = data.open_csv(file, 'inputs', ',')
    
    for i in df.index:
        if df['Category'][i] != 'Time' and type(df['Value'][i]) != np.float64:
            df['Value'][i] = float(df['Value'][i])
    
    return df
    

def get_settings(file):
    """ Get values and metadata from csv settings files in this directory and store them 
        into separate dictionaries 
    """
    df = get_values_df(file)
    
    df.index = df['Name']
    dic_value = df.to_dict()
    
    dic_meta = {}
    for n in df.index:
        meta = []
        for c in df.columns:
            if c != 'Name':
                meta.append(df[c][n])
            else:
                name = df['Name'][n]
        dic_meta[name] = meta
     
    return dic_value['Value'], dic_meta


def get_param(file, Categories):
    """ Get values and metadata from csv parameter files in this directory and store them 
        into separate dictionaries 
    """
    df = get_values_df(file)
    dic, dic_meta = {}, {}
    for c in Categories:
        dic[c] = {}
        dic_meta[c] = {}
    for i in df.index:
        meta = []
        for col in ['Units', 'Description', 'Source']:
                meta.append(df[col][i])
        dic_meta[df['Category'][i]][df['Name'][i]] = meta
        dic[df['Category'][i]][df['Name'][i]] = df['Value'][i]
     
    return dic, dic_meta, Categories
    

def make_param(category, name, value, meta, *subcategory):
    """ Passes the value and metadata of a given parameter into P and P_meta, given a Category
        and a name.
    """
    if category not in Categories:
        print('Error: {} was passed and is not in Categories'.format(category))
        return 
        
    if not subcategory:
        P[category][name] = value
        P_meta[category][name] = meta
    else:
        subcategory  = subcategory[0]
        try:
            P[category][subcategory][name] = value
        except KeyError:
            P[category][subcategory], P_meta[category][subcategory] = {}, {}
            P[category][subcategory][name] = value
        
        P_meta[category][subcategory][name] = meta
        

def time_param():
    """ Return the list of Periods, the number of Time_steps and the duration of the each
        time step dt, based on the given Time informations in the settings.csv file. The 
        units are in hours. Adds their value and metadata to P and P_meta.
    """
    # dt
    Description = 'Length of a timestep in hours'
    dt = datetime.strptime(S['Time_step'], S['Time_format']).time()
    if dt.hour != 0 and dt.minute == 0 and dt.second == 0:
        dt = dt.hour
    elif dt.hour == 0 and dt.minute != 0 and dt.second == 0:
        dt = dt.minute / 60
    else:
        print_error('Period_length')
    make_param('Time', 'dt', dt, ['hour', Description, 'calc'])
    
    start = S['Period_start'] + ' ' + S['Period_start_time']
    dt_start = datetime.strptime(start, Datetime_format)
    end = S['Period_end'] + ' ' + S['Period_start_time']
    dt_end = datetime.strptime(end, Datetime_format)
    
    # Time_steps
    Description = 'Number of timesteps'
    Time_steps = ((dt_end - dt_start).days * 24) / dt
    Time_steps_per_day = 24 / dt
    make_param('Time', 'Time_steps', Time_steps, ['integer', Description, 'calc'])
    
    # Periods
    Description = 'List of timestep index'
    if int(Time_steps) == Time_steps and int(Time_steps_per_day) == Time_steps_per_day:
        Periods = list(range(0, int(Time_steps)))
    else:
        print_error('time_step_int')
    make_param('Timedep', 'Periods', Periods, ['integer', Description, 'calc'])
    
    Days = []
    Description = 'List of days in a date format'
    Day_one = datetime.strptime(start, Datetime_format)
    for d in range(0, (dt_end - dt_start).days):
        Days.append(datetime.strftime(Day_one + timedelta(days=d), S['Date_format']))
    make_param('Time', 'Days', Days, ['-', Description, 'calc'])

    Time = []
    Description = 'hour:min:sec for each timestep in a day'
    for t in range(0, int(Time_steps_per_day)):
        Time.append(datetime.strftime(Day_one + timedelta(hours=t*dt), S['Time_format']))
    make_param('Timedep', 'Time', Time, ['-', Description, 'calc'])
    
    return Periods, Time_steps, dt, Days, Time, dt_end

    
def initialize_model():
    """ Return a blank Gurobi model and set solver timelimit """
    # Create a new model
    m = gp.Model("MIP_SFF_v0.31")
    # Remove previous model parameters and data
    m.resetParams()
    m.reset()
    # Set solver time limit
    m.setParam("TimeLimit", S['Solver_time_limit'])
    
    return m
        

# Parameter categories
Categories = ['AD', 'PV', 'BAT', 'SOFC', 'BOI', 'CGT', 'Eco', 'CO2', 'build', 'General', 'Time', 
              'Timedep']
# Dictionnaries of values and metadata from the file 'parameters.csv'
# example: P['AD']['eff'] = 0.3 and P_meta['AD']['eff'] = ['-', 'AD efficiency', 'energyscope']
P, P_meta, Categories = get_param('parameters.csv', Categories)
# Dictionnaries of values and metadata from the file 'Settings.csv'
S, S_meta = get_settings('settings.csv')
# List of periods, number of time steps and delta t (duration of a time step) in hours
Datetime_format = S['Date_format'] + ' ' + S['Time_format']
Periods, Time_steps, dt, Days, Time, dt_end = time_param()
# Default upper bound for most variables
Bound = S['Var_bound']
# Dictionnary of variable metadata
V_meta = {}
V_meta['Header'] = ['Name', 'Value', 'Lower Bound', 'Upper Bound', 'Units', 'Decription', 'Type']
V_bounds = {}
# Dictionnary describing each constraint and its source if applicable
C_meta = {}

m = initialize_model()