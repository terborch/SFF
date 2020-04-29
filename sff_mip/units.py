""" This module contains all functions necessary to model each unit
    #   TODO: add actual losses to battery (see Dirk's thesis)
    #   TODO: add discharge and charge rate limit to battery
    #   TODO: add depth of discharge limit to battery
    #   TODO: add self discharge to battery
    #   TODO: generalise storage unit variables
    #   TODO: add better aprox for biomass temperature
"""

# External modules
from gurobipy import GRB
# Internal modules
from initialize_model import m, P, Periods, P_meta, V_meta, C_meta, Bound, dt
import global_param


##################################################################################################
### Boiler
##################################################################################################


def boi(unit_prod, unit_cons, unit_size):
    c = 'BOI'
    n = 'BOI_production'
    C_meta[n] = ['Heat produced relative to Gas and Biogas consumed and Efficiency', 2]
    m.addConstrs(((unit_cons[('Biogas',p)] + unit_cons[('Gas',p)])*P[c]['Eff'] == 
                  unit_prod[('Heat',p)] for p in Periods), n);
    
    n = 'BOI_size'
    C_meta[n] = ['Upper limit on Heat produced relative to installed capacity', 3]
    m.addConstrs((unit_prod[('Heat',p)] <= unit_size for p in Periods), n);



##################################################################################################
### Photovoltaïc
##################################################################################################


def pv(unit_prod, unit_size, Irradiance):
    c = 'PV'
    n = 'PV_production'
    C_meta[n] = ['Elec produced relative to Irradiance, Efficiency and Installed capacity', 4]
    m.addConstrs((unit_prod[('Elec',p)] == Irradiance[p] * P[c]['Eff'] * unit_size 
                  for p in Periods), n);
    
    n = 'PV_roof_size'
    C_meta[n] = ['Upper limit on Installed capacity relative to Available area', 5]
    m.addConstr(unit_size <= P['build']['Ground_area'] * P['PV']['max_utilisation'], n);    
    
    
    
##################################################################################################
### Battery
##################################################################################################


def bat(unit_prod, unit_cons, unit_size, unit_SOC, unit_charge, unit_discharge):
    """ MILP model of a battery
        Charge and discharge efficiency follows Dirk Lauinge MA thesis
        Unit is force to cycle once a day
        TODO: Self discharge
        TODO: Discharge rate dependent on size and time step
    """
    
    # Parameters
    u = 'BAT'
    Eff = P[u]['Eff']**0.5
    
    # Constraints
    n = f'{u}_SOC'
    C_meta[n] = ['State of Charge detla relative to Produced and Consumed Elec and Efficiency', 5]
    m.addConstrs((unit_SOC[p + 1] - unit_SOC[p] ==  
                  (Eff*unit_cons[('Elec',p)] - (1/Eff)*unit_prod[('Elec',p)]) 
                  for p in Periods), n);
    
    n = f'{u}_charge_discharge'
    C_meta[n] = ['Prevent the unit from charging and discharging at the same time', 5]
    m.addConstrs((unit_charge[p] + unit_discharge[p] <= 1 for p in Periods), n);
    n = f'{u}_charge'
    C_meta[n] = ['M constraint to link the boolean variable Charge with Elec consumption', 5]
    m.addConstrs((unit_charge[p]*Bound >= unit_cons[('Elec',p)] for p in Periods), n);
    n = f'{u}_discharge'
    C_meta[n] = ['M constraint to link the boolean variable Discharge with Elec production', 5]
    m.addConstrs((unit_discharge[p]*Bound >= unit_prod[('Elec',p)] for p in Periods), n);
    
    n = f'{u}_daily_cycle'
    C_meta[n] = ['Cycling constraint for the State of Charge over the entire modelling Period', 5]
    m.addConstr((unit_SOC[0] == unit_SOC[Periods[-1]]), n);
    n = f'{u}_daily_initial'
    C_meta[n] = ['Set the initial State of Charge at 0', 5]
    m.addConstr((unit_SOC[0] == 0), n);
    
    n = f'{u}_size_SOC'
    C_meta[n] = ['Upper limit on the State of Charge relative to the Installed Capacity', 5]
    m.addConstrs((unit_SOC[p] <= unit_size for p in Periods), n);
    n = f'{u}_size_discharge'
    C_meta[n] = ['Upper limit on Elec produced relative to the Installed Capacity', 5]
    m.addConstrs((unit_prod[('Elec',p)] <= unit_size for p in Periods), n);
    n = f'{u}_size_charge'
    C_meta[n] = ['Upper limit on Elec consumed relative to the Installed Capacity', 5]
    m.addConstrs((unit_cons[('Elec',p)] <= unit_size for p in Periods), n);



##################################################################################################
### Anaerobic Digester
##################################################################################################


def ad(unit_prod, unit_cons, unit_size, unit_T, unit_install, Ext_T, Irradiance):
    # Parameters
    global_param.AD_dimentions(P, P_meta)
    
    c, g = 'AD', 'General'
    n = 'AD_production'
    C_meta[n] = ['Biogas produced relative to Biomass consumed and Efficiency', 5]
    m.addConstrs((unit_prod[('Biogas',p)] == 
                  unit_cons[('Biomass',p)]*P[c]['Eff'] for p in Periods), n);
    
    n = 'AD_elec_cons'
    C_meta[n] = ['Elec consumed relative to Biogas produced and Elec consumption factor', 5]
    m.addConstrs((unit_cons[('Elec',p)] == 
                  unit_prod[('Biogas',p)]*P[c]['Elec_cons'] for p in Periods), n);
    
    n = 'AD_size'
    C_meta[n] = ['Upper limit on Biogas produced relative to Installed capacity', 5]
    m.addConstrs((unit_prod[('Biogas',p)] <= unit_size for p in Periods), n);

    # Thermodynamics parameters
    n = 'U'
    P_meta[c][n] = ['kW/°C', 'AD heat conductance', 'calc']
    P[c][n] = P[c]['Cap_area']*P[c]['U_cap']*(1 + P[c]['U_wall'])
    
    n = 'C'
    P_meta[c][n] = ['kWh/°C', 'Heat capacity of the AD', 'calc']
    P[c][n] = P['General']['Cp_water']*P[c]['Sludge_volume'] + P['build']['C_b']*P[c]['Ground_area']
    
    # Thermodynamic variables   
    n = 'heat_loss_biomass'
    V_meta[n] = ['kW', 'Heat loss from biomass input', 'time']
    heat_loss_biomass = m.addVars(Periods, lb=0, ub=Bound, name= n)
    
    # Thermodynamic constraints 
    C_meta[n] = ['Heat losses relative to Biomass consumption and mean external temperature', 5]
    m.addConstrs((heat_loss_biomass[p] == ((unit_cons[('Biomass',p)]/P[c]['Manure_HHV_dry'])/
                  (1 - P[c]['Biomass_water'])/1000)*
                  P[g]['Cp_water']*(P[c]['T_mean'] - P[g]['Temp_ext_mean']) for p in Periods), n);
    
    P_meta[c]['Gains_solar'] = ['kW', 'Heat gains from irradiation', 'calc']
    Gains_solar_AD = [P[c]['Cap_abs']*P[c]['Ground_area']*Irradiance[p] for p in Periods]
    
    P_meta[c]['Gains_AD'] = ['kW', 'Sum of all heat gains', 'calc']
    Gains_AD = [unit_cons[('Elec',p)] + Gains_solar_AD[p] for p in Periods]
    
    n = 'AD_temperature'
    C_meta[n] = ['AD Temperature change relative to External Temperature, Gains and Losses', 5]
    m.addConstrs((P[c]['C']*(unit_T[p+1] - unit_T[p])/dt == P[c]['U']*(Ext_T[p] - unit_T[p]) +
                  Gains_AD[p] - heat_loss_biomass[p] + unit_cons[('Heat',p)] for p in Periods), n);
    
    n = 'AD_final_temperature'
    C_meta[n] = ['Cycling constraint for the AD Temperate over the entire modelling Period', 5]
    m.addConstr(unit_T[Periods[-1] + 1] == unit_T[0], n);
    
    # Add temperature constraints only if the the unit is installed
    V_meta[n] = ['°C', 'Minimum sludge temperature', 'unique']
    min_T_AD = m.addVar(lb=-Bound, ub=Bound, name='min_T_AD')
    V_meta[n] = ['°C', 'Maximum sludge temperature', 'unique']
    max_T_AD = m.addVar(lb=-Bound, ub=Bound, name='max_T_AD')
    
    n = 'AD_temperature_constraint'
    C_meta[n] = ['Limit AD Temperature only if AD is installed', 5]
    m.addGenConstrIndicator(unit_install, True, min_T_AD == P[c]['T_min'])
    m.addGenConstrIndicator(unit_install, True, max_T_AD == P[c]['T_max'])

    m.addConstrs((unit_T[p] >= min_T_AD for p in Periods), n);
    m.addConstrs((unit_T[p] <= max_T_AD for p in Periods), n);

##################################################################################################
### Solid Oxide Fuel Cell  
##################################################################################################


def sofc(unit_prod, unit_cons, unit_size):
    c = 'SOFC'
    n = 'SOFC_Elec_production'
    C_meta[n] = ['Elec produced relative to Biogas and gas consumed and Elec Efficiency', 6]
    m.addConstrs((unit_prod[('Elec',p)] == (unit_cons[('Biogas',p)] + unit_cons[('Gas',p)])*
                  (P[c]['Eff_elec'] - P[c]['GC_elec_frac']) for p in Periods), n);
    
    n = 'SOFC_Heat_production'
    C_meta[n] = ['Heat produced relative to Biogas and gas consumed and Heat Efficiency', 6]
    m.addConstrs((unit_prod[('Heat',p)] == (unit_cons[('Biogas',p)] + unit_cons[('Gas',p)])*
                  ((1 - P[c]['Eff_elec']) - P[c]['GC_elec_frac'])*P[c]['Eff_thermal'] 
                  for p in Periods), n);    
    
    n = 'SOFC_size'
    C_meta[n] = ['Upper limit on Elec produced relative to installed capacity', 6]
    m.addConstrs((unit_prod[('Elec',p)] <= unit_size for p in Periods), n);



##################################################################################################
### Compressed Gas Tank
##################################################################################################


def cgt(unit_prod, unit_cons, unit_size, unit_SOC, unit_charge, unit_discharge):
    """ MILP model of Compressed Gas Tank for storing Natural Gas. No losses are modeled.
        The tank only accepts Biogas and assumes the energy consumption and volume takeup
        to be equivalent between 1m^3 of Methane and 1m^3 of CO2
    """
    
    u = 'CGT'
    g = 'General'
    r = 'Biogas'
    
    # Constraints
    n = f'{u}_SOC'
    C_meta[n] = ['State of Charge detla relative to Produced and Consumed Gas', 5]
    m.addConstrs((unit_SOC[p + 1] - unit_SOC[p] == (unit_cons[(r,p)] - unit_prod[(r,p)])/
                  P[g]['Biogas_CH4'] for p in Periods), n);
    n = f'{u}_Compression_Elec'
    C_meta[n] = ['Electricity requiered to compress the Gas', 5]
    m.addConstrs((unit_cons[('Elec',p)] == unit_cons[(r,p)]*
                  P[u]['Elec_comp']/P[g]['Biogas_CH4'] for p in Periods), n);
    
    n = f'{u}_charge_discharge'
    C_meta[n] = ['Prevent the unit from charging and discharging at the same time', 5]
    m.addConstrs((unit_charge[p] + unit_discharge[p] <= 1 for p in Periods), n);
    n = f'{u}_charge'
    C_meta[n] = ['M constraint to link the boolean variable Charge with Gas consumption', 5]
    m.addConstrs((unit_charge[p]*Bound >= unit_cons[(r,p)] for p in Periods), n);
    n = f'{u}_discharge'
    C_meta[n] = ['M constraint to link the boolean variable Discharge with Gas production', 5]
    m.addConstrs((unit_discharge[p]*Bound >= unit_prod[(r,p)] for p in Periods), n);
    
    n = f'{u}_daily_cycle'
    C_meta[n] = ['Cycling constraint for the State of Charge over the entire modelling Period', 5]
    m.addConstr((unit_SOC[0] == unit_SOC[Periods[-1]]), n);
    n = f'{u}_daily_initial'
    C_meta[n] = ['Set the initial State of Charge at 0', 5]
    m.addConstr((unit_SOC[0] == 0), n);
    
    n = f'{u}_size_SOC'
    C_meta[n] = ['Upper limit on the State of Charge relative to the Installed Capacity', 5]
    m.addConstrs((unit_SOC[p] <= unit_size for p in Periods), n);
    n = f'{u}_size_discharge'
    C_meta[n] = ['Upper limit on Gas produced relative to the Installed Capacity', 5]
    m.addConstrs((unit_prod[(r,p)] <= unit_size for p in Periods), n);
    n = f'{u}_size_charge'
    C_meta[n] = ['Upper limit on Gas consumed relative to the Installed Capacity', 5]
    m.addConstrs((unit_cons[(r,p)] <= unit_size for p in Periods), n);

##################################################################################################
### END
##################################################################################################
