""" This module contains all functions necessary to model each unit
"""



##################################################################################################
### Photovoltaïc
##################################################################################################


def pv(m, P, unit_prod_t, unit_size, Periods, Irradiance):
    o = 'PV_production'
    m.addConstrs((unit_prod_t[('Elec',p)] == Irradiance[p] * P['PV_eff'] * unit_size 
                  for p in Periods), o);
    
    
    
##################################################################################################
### Battery
##################################################################################################


def bat(m, P, unit_prod_t, unit_cons_t, unit_size, Periods, Bound):
    # Variables
    bat_SOC_t = m.addVars(Periods + [24], lb = 0, ub = Bound, name = 'bat_SOC_t')
    
    # Constraints
    o = 'BAT_SOC'
    m.addConstrs((bat_SOC_t[p + 1] - bat_SOC_t[p] == P['BAT_eff'] * 
                  (unit_cons_t[('Elec',p)] - unit_prod_t[('Elec',p)]) for p in Periods), o);
    
    o = 'BAT_daily_cycle'
    m.addConstr((bat_SOC_t[0] == bat_SOC_t[24]), o);
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


def ad(m, P, unit_prod_t, unit_cons_t, unit_size, Periods):
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


def sofc(m, P, unit_prod_t, unit_cons_t, unit_size, Periods):
    o = 'SOFC_production'
    m.addConstrs((unit_prod_t[('Elec',p)] == unit_cons_t[('Biogas',p)]*
                  (P['SOFC_eff'] - P['GC_elec_frac']) for p in Periods), o);
    
    o = 'SOFC_size'
    m.addConstrs((unit_prod_t[('Elec',p)] <= unit_size for p in Periods), o);


