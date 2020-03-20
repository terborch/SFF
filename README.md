# EPFL Master Thesis - spring 2020
Energetic, Environmental and Economic Model of a Farm: Case study Swiss Future Farm

Optimization tool: Gurobi - Academic Licencs
Support for writing the optimization problem: Gurobipy - Jupyter Notebook - Spyer 4
Recommended jupyter extension: ndextensions - collapsable headings

## sff_mip module structure


1. inputs

All model inputs are in the inputs folder

* external contains weather data
* internal contains consumption profiles (TODO: include annual/monthly consumption values in here)
* economic contains unit related investment costs and resourse purchase and selling costs
* parameter.csv hold all other parameters with units and description
* settings.csv hold model settings such as variable bounds and unit max and min size

All inputs are stored in .csv files.