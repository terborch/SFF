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


##################################################################################################
### Boiler
##################################################################################################


def boi(unit_cons, unit_size, flow_t):
    o = 'PV_production'
    m.addConstrs((unit_cons[('Gas',p)] * P['BOI_eff'] == 
                  flow_t['m1',p] * (P['Th_boiler'] - P['Tc_boiler']) * P['Cp_water']
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
    bat_SOC_t = m.addVars(Periods + [Periods[-1] + 1], lb = 0, ub = Bound, name = 'bat_SOC_t')
    bat_charge_t = m.addVars(Periods, vtype=GRB.BINARY, name='bat_charge_t')
    bat_discharge_t = m.addVars(Periods, vtype=GRB.BINARY, name='bat_discharge_t')
    
    # Parameters
    eff = P['BAT_eff']**0.5
    
    # Constraints
    o = 'BAT_SOC'
    m.addConstrs((bat_SOC_t[p + 1] - bat_SOC_t[p] ==  
                  (eff*unit_cons[('Elec',p)] - (1/eff)*unit_prod[('Elec',p)]) 
                  for p in Periods), o);
    
    o = 'BAT_charge_discharge'
    m.addConstrs((bat_charge_t[p] + bat_discharge_t[p] <= 1 for p in Periods), o);
    o = 'BAT_charge'
    m.addConstrs((bat_charge_t[p]*Bound >= unit_cons[('Elec',p)] for p in Periods), o);
    o = 'BAT_discharge'
    m.addConstrs((bat_discharge_t[p]*Bound >= unit_prod[('Elec',p)] for p in Periods), o);
    
    o = 'BAT_daily_cycle'
    m.addConstr((bat_SOC_t[0] == bat_SOC_t[Periods[-1]]), o);
    o = 'BAT_daily_initial'
    m.addConstr((bat_SOC_t[0] == 0), o);
    
    o = 'BAT_size_SOC'
    m.addConstrs((bat_SOC_t[p] <= unit_size for p in Periods), o);
    o = 'BAT_size_discharge'
    m.addConstrs((unit_prod[('Elec',p)] <= unit_size for p in Periods), o);
    o = 'BAT_size_charge'
    m.addConstrs((unit_cons[('Elec',p)] <= unit_size for p in Periods), o);



##################################################################################################
### Anaerobic Digester
##################################################################################################


def ad(unit_prod, unit_cons, unit_size, Ext_T, Irradiance):
    o = 'AD_production'
    m.addConstrs((unit_prod[('Biogas',p)] == 
                  unit_cons[('Biomass',p)]*P['AD_eff'] for p in Periods), o);
    
    o = 'AD_elec_cons'
    m.addConstrs((unit_cons[('Elec',p)] == 
                  unit_prod[('Biogas',p)]*P['AD_elec_cons'] for p in Periods), o);
    
    o = 'AD_size'
    m.addConstrs((unit_prod[('Biogas',p)] <= unit_size for p in Periods), o);

    # Thermodynamics
    name = 'U_AD'
    P_meta[name] = ['kW/°C', 'AD heat conductance', 'AD']
    P[name] = P['AD_cap_area']*P['U_AD_cap']*(1 + P['U_AD_wall'])
    
    name = 'C_AD'
    P_meta[name] = ['kWh/°C', 'Heat capacity of the AD', 'AD']
    P[name] = P['Cp_water']*P['AD_sludge_volume'] + P['C_b']*P['AD_ground_area']
    
    o = 'T_AD_t'
    V_meta[o] = ['°C', 'Interior temperature of the AD']
    T_AD_t = m.addVars(Periods + [Periods[-1] + 1], lb=-1000, ub=1000, name= o)
    
    o = 'q_AD_t'
    q_AD_t = m.addVars(Periods, lb=0, ub=Bound, name= o)
    
    o = 'loss_biomass'
    V_meta[o] = ['kW', 'Heat loss from biomass input', 'calc', 'AD']
    loss_biomass = m.addVars(Periods, lb=0, ub=Bound, name= o)
    m.addConstrs(( loss_biomass[p] == ((unit_cons[('Biomass',p)]/P['Manure_HHV_dry'])/
                  (1 - P['Biomass_water'])/1000)*P['Cp_water']*(P['T_AD_mean'] - P['Temp_ext_mean']) for p in Periods), o);
    
    P_meta['Gains_solar_AD_t'] = ['kW', 'Heat gains from irradiation', 'calc', 'AD']
    Gains_solar_AD_t = [P['AD_cap_abs']*P['AD_ground_area']*Irradiance[p] for p in Periods]
    
    P_meta['Gains_AD_t'] = ['kW', 'Sum of all heat gains', 'calc', 'AD']
    Gains_AD_t = [unit_cons[('Elec',p)] + Gains_solar_AD_t[p] - loss_biomass[p] 
                  for p in Periods]
    
    o = 'AD_temperature'
    m.addConstrs((P['C_AD']*(T_AD_t[p+1] - T_AD_t[p])/dt == 
                  P['U_AD']*(Ext_T[p] - T_AD_t[p]) + Gains_AD_t[p] + q_AD_t[p]
                  for p in Periods), o);
    
    o = 'AD_final_temperature'
    m.addConstr( T_AD_t[Periods[-1] + 1] == T_AD_t[0], o);
    
    ###o = 'AD_temperature_constraint'
    ###m.addConstrs((T_AD_t[p] >= P['T_AD_min'] for p in Periods), o);
    ###m.addConstrs((T_AD_t[p] <= P['T_AD_max'] for p in Periods), o);
    


##################################################################################################
### Solid Oxide Fuel Cell  
##################################################################################################


def sofc(unit_prod, unit_cons, unit_size):
    o = 'SOFC_production'
    m.addConstrs((unit_prod[('Elec',p)] == unit_cons[('Biogas',p)]*
                  (P['SOFC_eff'] - P['GC_elec_frac']) for p in Periods), o);
    
    o = 'SOFC_size'
    m.addConstrs((unit_prod[('Elec',p)] <= unit_size for p in Periods), o);


##################################################################################################
### END
##################################################################################################
