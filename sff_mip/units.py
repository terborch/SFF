""" This module contains all functions necessary to model each unit
    #   TODO: add depth of discharge limit to battery
    #   TODO: add better aprox for biomass temperature
"""

# Internal modules
from read_inputs import P, C_meta, Bound

##################################################################################################
### Gas Boiler
##################################################################################################


def gboi(m, Days, Hours, unit_prod, unit_cons, unit_size):
    c = 'GBOI'
    n = 'GBOI_production'
    C_meta[n] = ['Heat produced relative to Gas and Biogas consumed and Efficiency', 0]
    m.addConstrs(((unit_cons['Biogas',d,h] + unit_cons['Gas',d,h])*P[c]['Eff'] == 
                  unit_prod['Heat',d,h] for d in Days for h in Hours), n);
    
    n = 'GBOI_size'
    C_meta[n] = ['Upper limit on Heat produced relative to installed capacity', 0]
    m.addConstrs((unit_prod['Heat',d,h] <= unit_size for d in Days for h in Hours), n);
    
   
    
##################################################################################################
### Wood Boiler
##################################################################################################


def wboi(m, Days, Hours, unit_prod, unit_cons, unit_size):
    c = 'WBOI'
    n = 'WBOI_production'
    C_meta[n] = ['Heat produced relative to Gas and Biogas consumed and Efficiency', 0]
    m.addConstrs((unit_cons['Wood',d,h]*P[c]['Eff'] == unit_prod['Heat',d,h] 
                  for d in Days for h in Hours), n);
    
    n = 'WBOI_size'
    C_meta[n] = ['Upper limit on Heat produced relative to installed capacity', 0]
    m.addConstrs((unit_prod['Heat',d,h] <= unit_size for d in Days for h in Hours), n);
    
    
    
##################################################################################################
### Electric Heater
##################################################################################################


def eh(m, Days, Hours, unit_prod, unit_cons, unit_size):
    c = 'EH'
    n = 'EH_production'
    C_meta[n] = ['Heat produced relative to Electricity consumed and Efficiency', 0]
    m.addConstrs((unit_cons['Elec',d,h]*P[c]['Eff'] == 
                  unit_prod['Heat',d,h] for d in Days for h in Hours), n);
    
    n = 'EH_size'
    C_meta[n] = ['Upper limit on Heat produced relative to installed capacity', 0]
    m.addConstrs((unit_prod['Heat',d,h] <= unit_size for d in Days for h in Hours), n);
    


###############################################################################
### Air-Air Heat Pump
###############################################################################


def ahp(m, Days, Hours, unit_prod, unit_cons, unit_size):
    """ MILP model of a Air Heat Pump with constant efficiency
        and fixed operating point. 
    """
    
    c = 'AHP'
    n = 'AHP_Heat_production'
    C_meta[n] = ['Heat produced relative to Elec consumed and COP', 0]
    m.addConstrs((unit_prod['Heat',d,h] == unit_cons['Elec',d,h]*P[c]['COP']
                   for d in Days for h in Hours), n);    
    
    n = 'AHP_size'
    C_meta[n] = ['Upper limit on Elec produced relative to installed capacity', 0]
    m.addConstrs((unit_prod['Heat',d,h] <= unit_size for d in Days for h in Hours), n);
    
    
    
##################################################################################################
### Photovoltaïc
##################################################################################################


def pv(m, Days, Hours, unit_prod, unit_size, Irradiance):
    c = 'PV'
    n = 'PV_production'
    C_meta[n] = ['Elec produced relative to Irradiance, Efficiency and Installed capacity', 5]
    m.addConstrs((unit_prod['Elec',d,h] == Irradiance[d,h] * P[c]['Eff'] * unit_size 
                  for d in Days for h in Hours), n);
    
    n = 'PV_roof_size'
    C_meta[n] = ['Upper limit on Installed capacity relative to Available area', 6]
    m.addConstr(unit_size <= P['Farm']['Ground_area'] * P['PV']['max_utilisation'], n);    
    
    
    
##################################################################################################
### Battery
##################################################################################################


def bat(m, Days, Hours, unit_prod, unit_cons, unit_size, unit_SOC, unit_charge, unit_discharge):
    """ MILP model of a battery
        Charge and discharge efficiency follows Dirk Lauinge MA thesis
        Unit is force to cycle once a day
        TODO: Discharge rate dependent on size and time step
    """
    
    # Parameters
    u = 'BAT'
    r = 'Elec'
    Eff = P[u]['Eff']**0.5

    # Constraints
    n = f'{u}_SOC'
    C_meta[n] = ['State of Charge detla relative to Produced and Consumed Elec and Efficiency', 0]
    m.addConstrs((unit_SOC[d,h + 1] - (1 - P[u]['Self_discharge'])*unit_SOC[d,h] ==  
                  (Eff*unit_cons[r,d,h] - (1/Eff)*unit_prod[r,d,h]) 
                  for d in Days for h in Hours), n);
    P[u]['Self_discharge']
    n = f'{u}_charge_discharge'
    C_meta[n] = ['Prevent the unit from charging and discharging at the same time', 0]
    m.addConstrs((unit_charge[d,h] + unit_discharge[d,h] <= 1 for d in Days for h in Hours), n);
    n = f'{u}_charge'
    C_meta[n] = ['M constraint to link the boolean variable Charge with Elec consumption', 0]
    m.addConstrs((unit_charge[d,h]*Bound >= unit_cons[r,d,h] for d in Days for h in Hours), n);
    n = f'{u}_discharge'
    C_meta[n] = ['M constraint to link the boolean variable Discharge with Elec production', 0]
    m.addConstrs((unit_discharge[d,h]*Bound >= unit_prod[r,d,h] for d in Days for h in Hours), n);
    
    n = f'{u}_daily_cycle'
    C_meta[n] = ['Cycling constraint on the battery SOC', 0]
    m.addConstrs((unit_SOC[d, Hours[-1]] == unit_SOC[d,Hours[-1] + 1] for d in Days), n);
    n = f'{u}_cycle_init'
    C_meta[n] = ['Cycling constraint to reset the battery SOC every day', 0]
    m.addConstrs((unit_SOC[d,0] == 0 for d in Days), n);
    
    n = f'{u}_size_SOC'
    C_meta[n] = ['Upper limit on the State of Charge relative to the Installed Capacity', 0]
    m.addConstrs((unit_SOC[d,h] <= unit_size for d in Days for h in Hours), n);
    n = f'{u}_size_discharge'
    C_meta[n] = ['Upper limit on Elec produced relative to the Installed Capacity', 0]
    m.addConstrs((unit_prod[r,d,h] <= unit_size for d in Days for h in Hours), n);
    n = f'{u}_size_charge'
    C_meta[n] = ['Upper limit on Elec consumed relative to the Installed Capacity', 0]
    m.addConstrs((unit_cons[r,d,h] <= unit_size for d in Days for h in Hours), n);



##################################################################################################
### Anaerobic Digester
##################################################################################################


def ad(m, Days, Hours, unit_prod, unit_cons, unit_size, AD_cons_Heat):
    
    c = 'AD'
    n = 'AD_production'
    C_meta[n] = ['Biogas produced relative to Biomass consumed and Efficiency', 0]
    m.addConstrs((unit_prod['Biogas',d,h] == 
                  unit_cons['Biomass',d,h]*P[c]['Eff'] for d in Days for h in Hours), n);
    
    n = 'AD_elec_cons'
    C_meta[n] = ['Elec consumed relative to Biogas produced and Elec consumption factor', 0]
    m.addConstrs((unit_cons['Elec',d,h] == 
                  unit_prod['Biogas',d,h]*P[c]['Elec_cons'] for d in Days for h in Hours), n);
    
    n = 'AD_size'
    C_meta[n] = ['Upper limit on Biogas produced relative to Installed capacity', 0]
    m.addConstrs((unit_prod['Biogas',d,h] <= unit_size for d in Days for h in Hours), n);

    n = 'AD_heat_cons'
    C_meta[n] = ['Heat consumed relative to AD size', 0]
    m.addConstrs((unit_cons['Heat',d,h] == (unit_size/P[c]['Capacity'])*
                  AD_cons_Heat[d,h] for d in Days for h in Hours), n);
        

###############################################################################
### Biogas cleaning for SOFC
###############################################################################

def gcsofc(m, Days, Hours, unit_prod, unit_cons, unit_size):
    """ MILP model of a Gas Cleaning installation for SOFC applications. The
        installation is a stack of filters to be replaced regularly, losses
        represent the electricity consumed by the fan and the chiller (drying).
    """
    Elec_cons = P['GCSOFC']['Elec_cons']*P['SOFC']['Eff_elec']
    
    n = 'GCSOFC_production'
    C_meta[n] = ['Biogas prod relative to Biogas cons', 0]
    m.addConstrs((unit_prod['Biogas',d,h] == unit_cons['Biogas',d,h] 
                  for d in Days for h in Hours), n);
    
    n = 'GCSOFC_Elec_cons'
    C_meta[n] = ['Electricity consumption relative to Biogas production', 0]
    m.addConstrs((unit_cons['Elec',d,h] == Elec_cons*unit_prod['Biogas',d,h]
                  for d in Days for h in Hours), n);
    
    n = 'GCSOFC_size'
    C_meta[n] = ['Upper limit on prod relative to installed capacity', 0]
    m.addConstrs((unit_prod['Biogas',d,h] <= unit_size for d in Days for h in Hours), n);

###############################################################################
### Solid Oxide Fuel Cell  
###############################################################################


def sofc(m, Days, Hours, unit_prod, unit_cons, unit_size):
    """ MILP model of a Solid Oxyde Fuel Cell (SOFC) with constant efficiency
        and fixed operating point. 
    """
    
    c = 'SOFC'
    n = 'SOFC_Elec_production'
    C_meta[n] = ['Elec produced relative to Biogas and gas consumed and Elec Efficiency', 6]
    m.addConstrs((unit_prod['Elec',d,h] == (unit_cons['Biogas',d,h] + unit_cons['Gas',d,h])*
                  P[c]['Eff_elec'] for d in Days for h in Hours), n);
    
    n = 'SOFC_Heat_production'
    C_meta[n] = ['Heat produced relative to Biogas and gas consumed and Heat Efficiency', 6]
    m.addConstrs((unit_prod['Heat',d,h] == (unit_cons['Biogas',d,h] + unit_cons['Gas',d,h])*
                  (1 - P[c]['Eff_elec'])*P[c]['Eff_thermal'] for d in Days for h in Hours), n);    
    
    n = 'SOFC_size'
    C_meta[n] = ['Upper limit on Elec produced relative to installed capacity', 6]
    m.addConstrs((unit_prod['Elec',d,h] <= unit_size for d in Days for h in Hours), n);


###############################################################################
### Internal COmbustion Engine
###############################################################################


def ice(m, Days, Hours, unit_prod, unit_cons, unit_size):
    """ MILP model of a Internal Combustion Engine (ICE) with constant efficiency
        and fixed operating point. 
    """
    
    c = 'ICE'
    n = 'ICE_Elec_production'
    C_meta[n] = ['Elec produced relative to Biogas and gas consumed and Elec Efficiency', 0]
    m.addConstrs((unit_prod['Elec',d,h] == (unit_cons['Biogas',d,h] + unit_cons['Gas',d,h])*
                  P[c]['Eff_elec'] for d in Days for h in Hours), n);
    
    n = 'ICE_Heat_production'
    C_meta[n] = ['Heat produced relative to Biogas and gas consumed and Heat Efficiency', 0]
    m.addConstrs((unit_prod['Heat',d,h] == (unit_cons['Biogas',d,h] + unit_cons['Gas',d,h])*
                  (1 - P[c]['Eff_elec'])*P[c]['Eff_thermal'] for d in Days for h in Hours), n);    
    
    n = 'ICE_size'
    C_meta[n] = ['Upper limit on Elec produced relative to installed capacity', 0]
    m.addConstrs((unit_prod['Elec',d,h] <= unit_size for d in Days for h in Hours), n);
    
    
###############################################################################
### Compressed Gas Tank
###############################################################################
    

def cgt(m, Periods, unit_prod, unit_cons, unit_size, unit_SOC, unit_charge, unit_discharge):
    """ MILP model of Compressed Gas Tank for storing Natural Gas. No losses are modeled.
        The tank only accepts Biogas and assumes the energy consumption and volume takeup
        to be equivalent between 1m^3 of Methane and 1m^3 of CO2
    """
    
    u = 'CGT'
    r = 'Biogas'
    
    # Constraints
    n = f'{u}_SOC'
    C_meta[n] = ['State of Charge detla relative to Produced and Consumed Gas', 0]
    m.addConstrs((unit_SOC[p + 1] - unit_SOC[p] == (unit_cons[(r,p)] - unit_prod[(r,p)])/
                  P['Physical']['Biogas_CH4'] for p in Periods), n);
    n = f'{u}_Compression_Elec'
    C_meta[n] = ['Electricity requiered to compress the Gas', 0]
    m.addConstrs((unit_cons[('Elec',p)] == unit_cons[(r,p)]*
                  P[u]['Elec_comp']/P['Physical']['Biogas_CH4'] for p in Periods), n);
    
    n = f'{u}_charge_discharge'
    C_meta[n] = ['Prevent the unit from charging and discharging at the same time', 0]
    m.addConstrs((unit_charge[p] + unit_discharge[p] <= 1 for p in Periods), n);
    n = f'{u}_charge'
    C_meta[n] = ['M constraint to link the boolean variable Charge with Gas consumption', 0]
    m.addConstrs((unit_charge[p]*Bound >= unit_cons[(r,p)] for p in Periods), n);
    n = f'{u}_discharge'
    C_meta[n] = ['M constraint to link the boolean variable Discharge with Gas production', 0]
    m.addConstrs((unit_discharge[p]*Bound >= unit_prod[(r,p)] for p in Periods), n);
    
    n = f'{u}_daily_cycle'
    C_meta[n] = ['Cycling constraint for the State of Charge over the entire modelling Period', 0]
    m.addConstr((unit_SOC[0] == unit_SOC[Periods[-1]]), n);
    n = f'{u}_daily_initial'
    C_meta[n] = ['Set the initial State of Charge at 0', 0]
    m.addConstr((unit_SOC[0] == 0), n);
    
    n = f'{u}_size_SOC'
    C_meta[n] = ['Upper limit on the State of Charge relative to the Installed Capacity', 0]
    m.addConstrs((unit_SOC[p] <= unit_size for p in Periods), n);
    n = f'{u}_size_discharge'
    C_meta[n] = ['Upper limit on Gas produced relative to the Installed Capacity', 0]
    m.addConstrs((unit_prod[(r,p)] <= unit_size for p in Periods), n);
    n = f'{u}_size_charge'
    C_meta[n] = ['Upper limit on Gas consumed relative to the Installed Capacity', 0]
    m.addConstrs((unit_cons[(r,p)] <= unit_size for p in Periods), n);

##################################################################################################
### END
##################################################################################################







##################################################################################################
### Anaerobic Digester
##################################################################################################

"""
def ad(m, Days, Hours, unit_prod, unit_cons, unit_size, unit_T, unit_install, Ext_T, Irradiance):
    
    c, g = 'AD', 'General'
    n = 'AD_production'
    C_meta[n] = ['Biogas produced relative to Biomass consumed and Efficiency', 0]
    m.addConstrs((unit_prod['Biogas',d,h] == 
                  unit_cons['Biomass',d,h]*P[c]['Eff'] for d in Days for h in Hours), n);
    
    n = 'AD_elec_cons'
    C_meta[n] = ['Elec consumed relative to Biogas produced and Elec consumption factor', 0]
    m.addConstrs((unit_cons['Elec',d,h] == 
                  unit_prod['Biogas',d,h]*P[c]['Elec_cons'] for d in Days for h in Hours), n);
    
    n = 'AD_size'
    C_meta[n] = ['Upper limit on Biogas produced relative to Installed capacity', 0]
    m.addConstrs((unit_prod['Biogas',d,h] <= unit_size for d in Days for h in Hours), n);

    # Thermodynamics parameters
    n = 'U'
    P_meta[c][n] = ['kW/°C', 'AD heat conductance', 'calc']
    P[c][n] = P[c]['Cap_area']*P[c]['U_cap']*(1 + P[c]['U_wall'])
    
    n = 'C'
    P_meta[c][n] = ['kWh/°C', 'Heat capacity of the AD', 'calc']
    P[c][n] = P['General']['Cp_water']*P[c]['Sludge_volume'] + P['build']['C_b']*P[c]['Ground_area']
    
    P_meta[c]['Gains_solar'] = ['kW', 'Heat gains from irradiation', 'calc']
    Gains_solar_AD = P[c]['Cap_abs']*P[c]['Ground_area']*Irradiance
    
    # Thermodynamic variables   
    n = 'heat_loss_biomass'
    V_meta[n] = ['kW', 'Heat loss from biomass input', 'time']
    heat_loss_biomass = m.addVars(Days, Hours, lb=0, ub=Bound, name= n)

    # Thermodynamic constraints 
    C_meta[n] = ['Heat losses relative to Biomass consumption and mean external temperature', 0]
    m.addConstrs((heat_loss_biomass[d,h] == ((unit_cons['Biomass',d,h]/P[c]['Manure_HHV_dry'])/
                  (1 - P[c]['Biomass_water'])/1000)*P[g]['Cp_water']*(P[c]['T_mean'] - P[g]['Temp_ext_mean']) 
                  for d in Days for h in Hours), n);
    
    n = 'AD_temperature'
    C_meta[n] = ['AD Temperature change relative to External Temperature, Gains and Losses', 0]
    m.addConstrs((P[c]['C']*(unit_T[d,h+1] - unit_T[d,h])/dt == P[c]['U']*(Ext_T[d,h] - unit_T[(d,h)]) +
                  Gains_solar_AD[d,h] + unit_cons['Elec',d,h] - heat_loss_biomass[d,h] + 
                  unit_cons['Heat',d,h] for d in Days for h in Hours), n);
    
    n = 'AD_T_daily_cycle'
    C_meta[n] = ['Cycling constraint for the AD temperature', 0]
    m.addConstrs((unit_T[d,Hours[-1]] == unit_T[d,Hours[-1] + 1] for d in Days), n);
    n = 'AD_T_daily_init'
    C_meta[n] = ['Fix the initial AD temperature every day', 0]
    m.addConstrs((unit_T[d,0] == P[c]['T_mean'] for d in Days), n);
    
    # Add temperature constraints only if the the unit is installed
    V_meta[n] = ['°C', 'Minimum sludge temperature', 'unique']
    min_T_AD = m.addVar(lb=-Bound, ub=Bound, name='min_T_AD')
    V_meta[n] = ['°C', 'Maximum sludge temperature', 'unique']
    max_T_AD = m.addVar(lb=-Bound, ub=Bound, name='max_T_AD')
    
    n = 'AD_temperature_constraint'
    C_meta[n] = ['Limit AD Temperature only if AD is installed', 0]
    m.addGenConstrIndicator(unit_install, True, min_T_AD == P[c]['T_min'])
    m.addGenConstrIndicator(unit_install, True, max_T_AD == P[c]['T_max'])
    
    m.addConstrs((unit_T[d,h] >= min_T_AD for d in Days for h in Hours), n);
    m.addConstrs((unit_T[d,h] <= max_T_AD for d in Days for h in Hours), n);
"""