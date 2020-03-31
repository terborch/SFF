""" This module contains all functions necessary to model each unit
    #   TODO: add actual losses to battery (see Dirk's thesis)
    #   TODO: add discharge and charge rate limit to battery
    #   TODO: add depth of discharge limit to battery
    #   TODO: add self discharge to battery
    #   TODO: generalise storage unit variables
"""

# External modules
from gurobipy import GRB
# Internal modules
from initialize_model import m, P, Periods


##################################################################################################
### Boiler
##################################################################################################


def boi(unit_cons_t, unit_size, flow_t):
    o = 'PV_production'
    m.addConstrs((unit_cons_t[('Gas',p)] * P['BOI_eff'] == 
                  flow_t['m1',p] * (P['Th_boiler'] - P['Tc_boiler']) * P['Cp_water']
                  for p in Periods), o);
    
    o = 'BOI_size'
    m.addConstrs((unit_cons_t[('Gas',p)]*P['BOI_eff'] <= unit_size for p in Periods), o);



##################################################################################################
### Photovoltaïc
##################################################################################################


def pv(unit_prod_t, unit_size, Irradiance):
    o = 'PV_production'
    m.addConstrs((unit_prod_t[('Elec',p)] == Irradiance[p] * P['PV_eff'] * unit_size 
                  for p in Periods), o);
    
    
    
##################################################################################################
### Battery
##################################################################################################


def bat(unit_prod_t, unit_cons_t, unit_size, Bound):
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
                  (eff*unit_cons_t[('Elec',p)] - (1/eff)*unit_prod_t[('Elec',p)]) 
                  for p in Periods), o);
    
    o = 'BAT_charge_discharge'
    m.addConstrs((bat_charge_t[p] + bat_discharge_t[p] <= 1 for p in Periods), o);
    o = 'BAT_charge'
    m.addConstrs((bat_charge_t[p]*Bound >= unit_cons_t[('Elec',p)] for p in Periods), o);
    o = 'BAT_discharge'
    m.addConstrs((bat_discharge_t[p]*Bound >= unit_prod_t[('Elec',p)] for p in Periods), o);
    
    o = 'BAT_daily_cycle'
    m.addConstr((bat_SOC_t[0] == bat_SOC_t[Periods[-1]]), o);
    o = 'BAT_daily_initial'
    m.addConstr((bat_SOC_t[0] == 0), o);
    
    o = 'BAT_size_SOC'
    m.addConstrs((bat_SOC_t[p] <= unit_size for p in Periods), o);
    o = 'BAT_size_discharge'
    m.addConstrs((unit_prod_t[('Elec',p)] <= unit_size for p in Periods), o);
    o = 'BAT_size_charge'
    m.addConstrs((unit_cons_t[('Elec',p)] <= unit_size for p in Periods), o);



##################################################################################################
### Anaerobic Digester
##################################################################################################


def ad(unit_prod_t, unit_cons_t, unit_size):
    o = 'AD_production'
    m.addConstrs((unit_prod_t[('Biogas',p)] == 
                  unit_cons_t[('Biomass',p)]*P['AD_eff'] for p in Periods), o);
    
    o = 'AD_elec_cons'
    m.addConstrs((unit_cons_t[('Elec',p)] == 
                  unit_prod_t[('Biogas',p)]*P['AD_elec_cons'] for p in Periods), o);
    
    o = 'AD_size'
    m.addConstrs((unit_prod_t[('Biogas',p)] <= unit_size for p in Periods), o);



##################################################################################################
### Solid Oxide Fuel Cell  
##################################################################################################


def sofc(unit_prod_t, unit_cons_t, unit_size):
    o = 'SOFC_production'
    m.addConstrs((unit_prod_t[('Elec',p)] == unit_cons_t[('Biogas',p)]*
                  (P['SOFC_eff'] - P['GC_elec_frac']) for p in Periods), o);
    
    o = 'SOFC_size'
    m.addConstrs((unit_prod_t[('Elec',p)] <= unit_size for p in Periods), o);


##################################################################################################
### END
##################################################################################################
