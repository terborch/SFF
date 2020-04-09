"""
### Model setup and initialization
    #   get parameter values from Parameters.csv
    #   get settings values from Settings.csv
    #   create global dictionaries of calculated parameters and units of model variables 
    #   initialize the global Gurobi MILP model called m
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
    

def get_param(file):
    """ Get values and metadata from csv files in this directory and store them 
        into separate dictionaries 
    """
    df = data.open_csv(file, 'inputs', ',')

    # Change every value into float format except the values in category Time
    for i in df.index:
        if df['Category'][i] != 'Time' and type(df['Value'][i]) != np.float64:
            df['Value'][i] = float(df['Value'][i])
    
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
    

def time_param():
    """ Return the list of Periods, the number of Time_steps and the duration of the each
        time step dt, based on the given Time informations in the settings.csv file. The 
        units are in hours.
    """
    dt = datetime.strptime(S['Time_step'], S['Time_format']).time()
    if dt.hour != 0 and dt.minute == 0 and dt.second == 0:
        dt = dt.hour
    elif dt.hour == 0 and dt.minute != 0 and dt.second == 0:
        dt = dt.minute / 60
    else:
        print_error('Period_length')
    
    start = S['Period_start'] + ' ' + S['Period_start_time']
    dt_start = datetime.strptime(start, Datetime_format)
    end = S['Period_end'] + ' ' + S['Period_start_time']
    dt_end = datetime.strptime(end, Datetime_format)

    Time_steps = ((dt_end - dt_start).days * 24) / dt
    Time_steps_per_day = 24 / dt
    
    if int(Time_steps) == Time_steps and int(Time_steps_per_day) == Time_steps_per_day:
        Periods = list(range(0, int(Time_steps)))
    else:
        print_error('time_step_int')
        
        
    Days = []
    Day_one = datetime.strptime(start, Datetime_format)
    for d in range(0, (dt_end - dt_start).days):
        Days.append(datetime.strftime(Day_one + timedelta(days=d), S['Date_format']))
    
    Time = []
    for t in range(0, int(Time_steps_per_day)):
        Time.append(datetime.strftime(Day_one + timedelta(hours=t*dt), S['Time_format']))
    
    return Periods, Time_steps, dt, Days, Time

    
def intialize_model():
    """ Return a blank Gurobi model and set solver timelimit """
    # Create a new model
    m = gp.Model("MIP_SFF_v0.25")
    # Remove previous model parameters and data
    m.resetParams()
    m.reset()
    # Set solver time limit
    m.setParam("TimeLimit", S['Solver_time_limit'])
    
    return m


# Dictionnaries of values and metadata from the file 'parameters.csv'
P, P_meta = get_param('parameters.csv')
# Dictionnaries of values and metadata from the file 'Settings.csv'
S, S_meta = get_param('settings.csv')
# List of periods, number of time steps and delta t (duration of a time step) in hours
Datetime_format = S['Date_format'] + ' ' + S['Time_format']
Periods, Time_steps, dt, Days, Time = time_param()
# Default upper bound for most variables
Bound = S['Var_bound']
# Dictionnary of the min, max and average value of time dependent parameters
P_t = {}
# Dictionnary of the units of variables and their description
V_meta = {}
# Dictionnary describing each constraint and its source if applicable
C_meta = {}

m = intialize_model()