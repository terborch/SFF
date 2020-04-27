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
from initialize_model import m, P, Periods, P_meta, V_meta, Bound, dt
import global_param


##################################################################################################
### Boiler
##################################################################################################


def boi(unit_prod, unit_cons, unit_size):
    c = 'BOI'
    n = 'BOI_production'
    m.addConstrs(((unit_cons[('Biogas',p)] + unit_cons[('Gas',p)])*P[c]['Eff'] == 
                  unit_prod[('Heat',p)] for p in Periods), n);
    
    n = 'BOI_size'
    m.addConstrs((unit_prod[('Heat',p)] <= unit_size for p in Periods), n);



##################################################################################################
### Photovoltaïc
##################################################################################################


def pv(unit_prod, unit_size, Irradiance):
    c = 'PV'
    n = 'PV_production'
    m.addConstrs((unit_prod[('Elec',p)] == Irradiance[p] * P[c]['Eff'] * unit_size 
                  for p in Periods), n);
    
    n = 'PV_roof_size'
    m.addConstr(unit_size <= P['build']['Heated_area']/(2), n);    
    
    
    
##################################################################################################
### Battery
##################################################################################################


def bat(unit_prod, unit_cons, unit_size):
    """ MILP model of a battery
        Charge and discharge efficiency follows Dirk Lauinge MA thesis
        Unit is force to cycle once a day
        TODO: Self discharge
        TODO: Discharge rate dependent on size and time step
    """
    # Variables
    bat_SOC = m.addVars(Periods + [Periods[-1] + 1], lb = 0, ub = Bound, name = 'bat_SOC')
    bat_charge = m.addVars(Periods, vtype=GRB.BINARY, name='bat_charge')
    bat_discharge = m.addVars(Periods, vtype=GRB.BINARY, name='bat_discharge')
    
    # Parameters
    c = 'BAT'
    Eff = P[c]['Eff']**0.5
    
    # Constraints
    n = 'BAT_SOC'
    m.addConstrs((bat_SOC[p + 1] - bat_SOC[p] ==  
                  (Eff*unit_cons[('Elec',p)] - (1/Eff)*unit_prod[('Elec',p)]) 
                  for p in Periods), n);
    
    n = 'BAT_charge_discharge'
    m.addConstrs((bat_charge[p] + bat_discharge[p] <= 1 for p in Periods), n);
    n = 'BAT_charge'
    m.addConstrs((bat_charge[p]*Bound >= unit_cons[('Elec',p)] for p in Periods), n);
    n = 'BAT_discharge'
    m.addConstrs((bat_discharge[p]*Bound >= unit_prod[('Elec',p)] for p in Periods), n);
    
    n = 'BAT_daily_cycle'
    m.addConstr((bat_SOC[0] == bat_SOC[Periods[-1]]), n);
    n = 'BAT_daily_initial'
    m.addConstr((bat_SOC[0] == 0), n);
    
    n = 'BAT_size_SOC'
    m.addConstrs((bat_SOC[p] <= unit_size for p in Periods), n);
    n = 'BAT_size_discharge'
    m.addConstrs((unit_prod[('Elec',p)] <= unit_size for p in Periods), n);
    n = 'BAT_size_charge'
    m.addConstrs((unit_cons[('Elec',p)] <= unit_size for p in Periods), n);



##################################################################################################
### Anaerobic Digester
##################################################################################################


def ad(unit_prod, unit_cons, unit_size, unit_T, unit_install, Ext_T, Irradiance):
    # Parameters
    global_param.AD_dimentions(P, P_meta)
    
    c, g = 'AD', 'General'
    n = 'AD_production'
    m.addConstrs((unit_prod[('Biogas',p)] == 
                  unit_cons[('Biomass',p)]*P[c]['Eff'] for p in Periods), n);
    
    n = 'AD_elec_cons'
    m.addConstrs((unit_cons[('Elec',p)] == 
                  unit_prod[('Biogas',p)]*P[c]['Elec_cons'] for p in Periods), n);
    
    n = 'AD_size'
    m.addConstrs((unit_prod[('Biogas',p)] <= unit_size for p in Periods), n);

    # Thermodynamics parameters
    name = 'U'
    P_meta[c][name] = ['kW/°C', 'AD heat conductance', 'calc']
    P[c][name] = P[c]['Cap_area']*P[c]['U_cap']*(1 + P[c]['U_wall'])
    
    name = 'C'
    P_meta[c][name] = ['kWh/°C', 'Heat capacity of the AD', 'calc']
    P[c][name] = P['General']['Cp_water']*P[c]['Sludge_volume'] + P['build']['C_b']*P[c]['Ground_area']
    
    # Thermodynamics variables   
    n = 'heat_loss_biomass'
    V_meta[n] = ['kW', 'Heat loss from biomass input', 'time']
    heat_loss_biomass = m.addVars(Periods, lb=0, ub=Bound, name= n)
    
    m.addConstrs(( heat_loss_biomass[p] == ((unit_cons[('Biomass',p)]/P[c]['Manure_HHV_dry'])/
                  (1 - P[c]['Biomass_water'])/1000)*
                  P[g]['Cp_water']*(P[c]['T_mean'] - P[g]['Temp_ext_mean']) for p in Periods), n);
    
    P_meta[c]['Gains_solar'] = ['kW', 'Heat gains from irradiation', 'calc']
    Gains_solar_AD = [P[c]['Cap_abs']*P[c]['Ground_area']*Irradiance[p] for p in Periods]
    
    P_meta[c]['Gains_AD'] = ['kW', 'Sum of all heat gains', 'calc']
    Gains_AD = [unit_cons[('Elec',p)] + Gains_solar_AD[p] for p in Periods]
    
    n = 'AD_temperature'
    m.addConstrs((P[c]['C']*(unit_T[p+1] - unit_T[p])/dt == P[c]['U']*(Ext_T[p] - unit_T[p]) +
                  Gains_AD[p] - heat_loss_biomass[p] + unit_cons[('Heat',p)] for p in Periods), n);
    
    n = 'AD_final_temperature'
    m.addConstr( unit_T[Periods[-1] + 1] == unit_T[0], n);
    
    # Add temperature constraints only if the the unit is installed
    min_T_AD = m.addVar(lb = -Bound, ub = Bound, name = 'min_T_AD')
    max_T_AD = m.addVar(lb = -Bound, ub = Bound, name = 'max_T_AD')
    
    n = 'AD_temperature_constraint'
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
    m.addConstrs((unit_prod[('Elec',p)] == (unit_cons[('Biogas',p)] + unit_cons[('Gas',p)])*
                  (P[c]['Eff_elec'] - P[c]['GC_elec_frac']) for p in Periods), n);
    
    n = 'SOFC_Heat_production'
    m.addConstrs((unit_prod[('Heat',p)] == (unit_cons[('Biogas',p)] + unit_cons[('Gas',p)])*
                  ((1 - P[c]['Eff_elec']) - P[c]['GC_elec_frac'])*P[c]['Eff_thermal'] 
                  for p in Periods), n);    
    
    n = 'SOFC_size'
    m.addConstrs((unit_prod[('Elec',p)] <= unit_size for p in Periods), n);


##################################################################################################
### END
##################################################################################################
