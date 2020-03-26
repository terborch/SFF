# EPFL Master Thesis - spring 2020
Energetic, Environmental and Economic Model of a Farm: Case study Swiss Future Farm

Optimization tool: Gurobi - Academic Licencs

Support for writing the optimization problem: Gurobipy - Jupyter Notebook - Spyer 4

Recommended jupyter extension: ndextensions - collapsable headings

## sff_mip module structure


### 1. inputs

All model inputs are in the inputs folder

* external contains weather data
* internal contains consumption profiles (TODO: include annual/monthly consumption values in here)
* economic contains unit related investment costs and resourse purchase and selling costs
* parameter.csv hold all other parameters with thier units and description
* settings.csv hold model settings such as variable bounds and unit max and min size

All inputs are stored in .csv files. They can be displayed as dataframes (for fixed inputs) and as graphs (for time dependent inputs) using the module data.py

### 2. model

The module model.py build the MIP optimization model. Here is a summary of how it does it.

* It calls on the module data.py to get data from the inputs folder (TODO: move parameter and settings inputs handling to data.py)
* It calls on the module initialize_model.py to create a global entity called m that contains the MIP
* It calls on the module initialize_model.py to declare global parameters and settings from parameters.csv and settings.csv
* It calls on the modules global_set.py to declare sets of units, resources and timesets
* global_param.py to declare global parameters economic and time dependent
* global_var.py to declare global variables mostly for units
* It calls on the module units.py to model each unit. units.py will in turn call the global objects necessary
* TODO: describe the thermodynamics of the farm
* The Masse and Energy balance is described
* TODO: heat cascade
* The CAPEX OPEX and TOTEX is calculated
* the function run will set the objective (TODO: objective selection) and solve the model m

### 3. outputs

The module results.py can be called to display and or save the time independent results in dataframes and the time dependent results as graphs. All results are stored in the pickle format. (TODO: save graphs, option for .csv format, unique folder for each run)


## Using the module

The file run.py allow the user to call on model.py to run and solve the model according to the parameters in the input folder and display the results of the optimization.

To facilitate tracking of parameters and variables and settings, it is possible to use the dictionnairies P, P_meta, S, S_meta, and V_meta containt values and metada such as units, description source and category.

TODO: lots of things todo in the run.py file, options to display inputs, save outputs, options to change inputs, iterative solving, time solving process at the python level, set what input file to use, option to save inputs along with outputs, option to save the model as .lp file...  

## HowTo install and run the module.

This module was created on windows 10 using Spyder 4 from Anaconda. It should run on Mac and Linux as well

1. Installing anaconda https://www.anaconda.com/distribution/

2. Run the anaconda command consol

3. Navigate to the module folder sff_mip in the consol

4. Install anaconda the environment sff_mip using the provided .yml file (only few external packages are used) and the following command: conda env create -f environment.yml

5. Activate the environment using this command: conda activate sff_mip

6. Run Spyder (or any other IDE you'd like) using this command: spyder

7. Alternatively run jupyter notebook using this command: jupyter notebook
and open the only notebook in the folder called run. This is also usefull for testing bits of code
