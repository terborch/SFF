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
    o = 'PV_production'
    m.addConstrs((unit_cons[('Gas',p)] * P['BOI_eff'] == unit_prod[('Heat',p)]
                  for p in Periods), o);
    
    o = 'BOI_size'
    m.addConstrs((unit_cons[('Gas',p)]*P['BOI_eff'] <= unit_size for p in Periods), o);



##################################################################################################
### Photovoltaïc
##################################################################################################


def pv(unit_prod, unit_size, Irradiance):
    o = 'PV_production'
    m.addConstrs((unit_prod[('Elec',p)] == Irradiance[p] * P['PV_eff'] * unit_size 
                  for p in Periods), o);
    
    
    
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
    eff = P['BAT_eff']**0.5
    
    # Constraints
    o = 'BAT_SOC'
    m.addConstrs((bat_SOC[p + 1] - bat_SOC[p] ==  
                  (eff*unit_cons[('Elec',p)] - (1/eff)*unit_prod[('Elec',p)]) 
                  for p in Periods), o);
    
    o = 'BAT_charge_discharge'
    m.addConstrs((bat_charge[p] + bat_discharge[p] <= 1 for p in Periods), o);
    o = 'BAT_charge'
    m.addConstrs((bat_charge[p]*Bound >= unit_cons[('Elec',p)] for p in Periods), o);
    o = 'BAT_discharge'
    m.addConstrs((bat_discharge[p]*Bound >= unit_prod[('Elec',p)] for p in Periods), o);
    
    o = 'BAT_daily_cycle'
    m.addConstr((bat_SOC[0] == bat_SOC[Periods[-1]]), o);
    o = 'BAT_daily_initial'
    m.addConstr((bat_SOC[0] == 0), o);
    
    o = 'BAT_size_SOC'
    m.addConstrs((bat_SOC[p] <= unit_size for p in Periods), o);
    o = 'BAT_size_discharge'
    m.addConstrs((unit_prod[('Elec',p)] <= unit_size for p in Periods), o);
    o = 'BAT_size_charge'
    m.addConstrs((unit_cons[('Elec',p)] <= unit_size for p in Periods), o);



##################################################################################################
### Anaerobic Digester
##################################################################################################


def ad(unit_prod, unit_cons, unit_size, unit_T, unit_install, Ext_T, Irradiance):
    # Parameters
    global_param.AD_dimentions(P, P_meta)
    
    o = 'AD_production'
    m.addConstrs((unit_prod[('Biogas',p)] == 
                  unit_cons[('Biomass',p)]*P['AD_eff'] for p in Periods), o);
    
    o = 'AD_elec_cons'
    m.addConstrs((unit_cons[('Elec',p)] == 
                  unit_prod[('Biogas',p)]*P['AD_elec_cons'] for p in Periods), o);
    
    o = 'AD_size'
    m.addConstrs((unit_prod[('Biogas',p)] <= unit_size for p in Periods), o);

    # Thermodynamics parameters
    name = 'U_AD'
    P_meta[name] = ['kW/°C', 'AD heat conductance', 'AD']
    P[name] = P['AD_cap_area']*P['U_AD_cap']*(1 + P['U_AD_wall'])
    
    name = 'C_AD'
    P_meta[name] = ['kWh/°C', 'Heat capacity of the AD', 'AD']
    P[name] = P['Cp_water']*P['AD_sludge_volume'] + P['C_b']*P['AD_ground_area']
    
    # Thermodynamics variables   
    o = 'heat_loss_biomass'
    V_meta[o] = ['kW', 'Heat loss from biomass input', 'calc', 'AD']
    heat_loss_biomass = m.addVars(Periods, lb=0, ub=Bound, name= o)
    
    m.addConstrs(( heat_loss_biomass[p] == ((unit_cons[('Biomass',p)]/P['Manure_HHV_dry'])/
                  (1 - P['Biomass_water'])/1000)*P['Cp_water']*(P['T_AD_mean'] - P['Temp_ext_mean']) 
                  for p in Periods), o);
    
    P_meta['Gains_solar_AD'] = ['kW', 'Heat gains from irradiation', 'calc', 'AD']
    Gains_solar_AD = [P['AD_cap_abs']*P['AD_ground_area']*Irradiance[p] for p in Periods]
    
    P_meta['Gains_AD'] = ['kW', 'Sum of all heat gains', 'calc', 'AD']
    Gains_AD = [unit_cons[('Elec',p)] + Gains_solar_AD[p] for p in Periods]
    
    o = 'AD_temperature'
    m.addConstrs((P['C_AD']*(unit_T[p+1] - unit_T[p])/dt == P['U_AD']*(Ext_T[p] - unit_T[p]) +
                  Gains_AD[p] - heat_loss_biomass[p] + unit_cons[('Heat',p)] for p in Periods), o);
    
    o = 'AD_final_temperature'
    m.addConstr( unit_T[Periods[-1] + 1] == unit_T[0], o);
    
    

    
    # Add temperature constraints only if the the unit is installed
    min_T_AD = m.addVar(lb = -Bound, ub = Bound, name = 'min_T_AD')
    max_T_AD = m.addVar(lb = -Bound, ub = Bound, name = 'max_T_AD')
    
    o = 'AD_temperature_constraint'
    m.addGenConstrIndicator(unit_install, True, min_T_AD == P['T_AD_min'])
    m.addGenConstrIndicator(unit_install, True, max_T_AD == P['T_AD_max'])

    m.addConstrs((unit_T[p] >= min_T_AD for p in Periods), o);
    m.addConstrs((unit_T[p] <= max_T_AD for p in Periods), o);

##################################################################################################
### Solid Oxide Fuel Cell  
##################################################################################################


def sofc(unit_prod, unit_cons, unit_size):
    o = 'SOFC_Elec_production'
    m.addConstrs((unit_prod[('Elec',p)] == (unit_cons[('Biogas',p)] + unit_cons[('Gas',p)])*
                  (P['SOFC_eff'] - P['GC_elec_frac']) for p in Periods), o);
    
    o = 'SOFC_Heat_production'
    m.addConstrs((unit_prod[('Heat',p)] == unit_cons[('Biogas',p)]*
                  ((1 - P['SOFC_eff']) - P['GC_elec_frac']) for p in Periods), o);    
    
    o = 'SOFC_size'
    m.addConstrs((unit_prod[('Elec',p)] <= unit_size for p in Periods), o);


##################################################################################################
### END
##################################################################################################
