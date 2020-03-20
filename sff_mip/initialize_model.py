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
# Internal modules
import data

def get_param(file):
    """ Get values and metadata from csv files in this directory and store them 
        into separate dictionaries 
    """
    df = data.open_csv(file, 'inputs', ',')

    # Change every value into float format except the values in category Time
    for i in df.index:
        if df['Category'][i] != 'Time' and  type(df['Value'][i]) != np.float64:
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
# Default upper bound for most variables
Bound = S['Var_bound']
# Dictionnary of the units of variables and their description
V_meta = {}
# Dictionnary describing each constraint and its source if applicable
C_meta = {}

m = intialize_model()