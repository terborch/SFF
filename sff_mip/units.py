""" This module contains all functions necessary to model each unit
    #   TODO: add depth of discharge limit to battery
"""

# Internal modules
from read_inputs import C_meta, Bound, Time_period_map

def t(*args):
    """ Given a resource (optional) and a Period key return the corresponding
        Day - Hour keys with the resource pre-pended
    """
    p = args[-1]
    if type(args[0]) == str:
        return args[0], Time_period_map[p][0], Time_period_map[p][1]
    else:
        return Time_period_map[p]

###############################################################################
### Gas Boiler - Heater
###############################################################################


def gboi(m, Days, Hours, unit_prod, unit_cons, unit_size, P):
    """ LP model of a Natural Gas Boiler efficiency is the same for any fuel """
    n = 'GBOI_production'
    C_meta[n] = ['Heat produced relative fuel consumed and Efficiency', 14]
    m.addConstrs((unit_prod['Heat',d,h] == P['GBOI','Eff']*(
        unit_cons['Biogas',d,h] + unit_cons['Gas',d,h] + unit_cons['BM',d,h]) 
        for d in Days for h in Hours), n);
    
    n = 'GBOI_size'
    C_meta[n] = ['Upper limit on Heat produced relative to installed capacity', 15]
    m.addConstrs((unit_prod['Heat',d,h] <= unit_size for d in Days for h in Hours), n);
    
   
    
###############################################################################
### Wood Boiler - Heater
###############################################################################


def wboi(m, Days, Hours, unit_prod, unit_cons, unit_size, P):
    """ LP model of a Wood Boiler """
    n = 'WBOI_production'
    C_meta[n] = ['Heat produced relative to consumed and Efficiency', 16]
    m.addConstrs((unit_prod['Heat',d,h] == P['WBOI','Eff']*unit_cons['Wood',d,h] 
                  for d in Days for h in Hours), n);
    
    n = 'WBOI_size'
    C_meta[n] = ['Upper limit on Heat produced relative to installed capacity', 14]
    m.addConstrs((unit_prod['Heat',d,h] <= unit_size for d in Days for h in Hours), n);
    
    
    
###############################################################################
### Air-Air Heat Pump - Heater
###############################################################################


def ahp(m, Days, Hours, unit_prod, unit_cons, unit_size, P):
    """ LP model of a Air Heat Pump with constant efficiency
        and fixed operating point. Domestic unit operating between external and
        internal air.
    """
    u = 'AHP'
    n = f'{u}_Heat_production'
    C_meta[n] = ['Heat produced relative to Elec consumed and COP', 18]
    m.addConstrs((unit_prod['Heat',d,h] == P[u,'COP']*unit_cons['Elec',d,h]
                   for d in Days for h in Hours), n);    
    
    n = f'{u}_size'
    C_meta[n] = ['Upper limit on Elec produced relative to installed capacity', 19]
    m.addConstrs((unit_cons['Elec',d,h] <= unit_size for d in Days for h in Hours), n);
    
    

###############################################################################
### Gothermal Heat Pump - Heater
###############################################################################


def ghp(m, Days, Hours, unit_prod, unit_cons, unit_size, P):
    """ LP model of a Gothermal Heat Pump with constant efficiency
        and fixed operating point. Disctric unit for a small housing apartement
        operating with a closed loop ground water heating system. Aprox.
        100m deep in Switzerland in the plateau region (500m altitude).
    """
    
    u = 'GHP'
    n = f'{u}_Heat_production'
    C_meta[n] = ['Heat produced relative to Elec consumed and COP', 20]
    m.addConstrs((unit_prod['Heat',d,h] == P[u,'COP']*unit_cons['Elec',d,h]
                   for d in Days for h in Hours), n);    
    
    n =  f'{u}_size'
    C_meta[n] = ['Upper limit on Elec produced relative to installed capacity', 21]
    m.addConstrs((unit_prod['Heat',d,h] <= unit_size for d in Days for h in Hours), n);


    
###############################################################################
### Electric Heater - Heater
###############################################################################
    

def eh(m, Days, Hours, unit_prod, unit_cons, unit_size, P):
    """ LP model of a Electric Heater """
    n = 'EH_production'
    C_meta[n] = ['Heat produced relative to Elec consumed and Efficiency', 22]
    m.addConstrs((unit_prod['Heat',d,h] == P['EH','Eff']*unit_cons['Elec',d,h]
                  for d in Days for h in Hours), n);
    
    n = 'EH_size'
    C_meta[n] = ['Upper limit on Heat produced relative to installed capacity', 15]
    m.addConstrs((unit_prod['Heat',d,h] <= unit_size for d in Days for h in Hours), n);
    
    

###############################################################################
### Solid Oxide Fuel Cell - Cogeneration
###############################################################################


def sofc(m, Days, Hours, unit_prod, unit_cons, unit_size, P):
    """ LP model of a Solid Oxyde Fuel Cell (SOFC) with constant efficiency
        and fixed operating point. Two efficiencies, one for NG amd BM and 
        another lower for BG because of CO2 content. 
    """
    
    c = 'SOFC'
    Eff_th_b = (1 - P[c,'Eff_elec_biogas'])*P[c,'Eff_thermal']
    Eff_th_ng = (1 - P[c,'Eff_elec_gas'])*P[c,'Eff_thermal']
    n = 'SOFC_Elec_production'
    C_meta[n] = ['Elec produced relative to fuel consumed and Eff', 23]
    m.addConstrs((unit_prod['Elec',d,h] == 
                  P[c,'Eff_elec_biogas']*unit_cons['Biogas',d,h] + 
                  P[c,'Eff_elec_gas']*(unit_cons['Gas',d,h] + unit_cons['BM',d,h])
                  for d in Days for h in Hours), n);
    
    n = 'SOFC_Heat_production'
    C_meta[n] = ['Heat produced relative to fuel cons and Heat eff', 24]
    m.addConstrs((unit_prod['Heat',d,h] == Eff_th_b*unit_cons['Biogas',d,h] + 
                  Eff_th_ng*(unit_cons['Gas',d,h] + unit_cons['BM',d,h])
                  for d in Days for h in Hours), n);    
    
    n = 'SOFC_size'
    C_meta[n] = ['Upper limit on Elec produced relative to installed capacity', 25]
    m.addConstrs((unit_prod['Elec',d,h] <= unit_size for d in Days for h in Hours), n);



###############################################################################
### Internal COmbustion Engine - Cogeneration
###############################################################################


def ice(m, Days, Hours, unit_prod, unit_cons, unit_size, P):
    """ MILP model of a Internal Combustion Engine (ICE) with constant efficiency
        and fixed operating point. 
    """
    c = 'ICE'
    n = 'ICE_Elec_production'
    C_meta[n] = ['Elec produced relative to fuel cons and Elec eff', 26]
    m.addConstrs((unit_prod['Elec',d,h] == (
        unit_cons['Biogas',d,h] + unit_cons['Gas',d,h] + unit_cons['BM',d,h])*
                  P[c,'Eff_elec'] for d in Days for h in Hours), n);
    
    n = 'ICE_Heat_production'
    C_meta[n] = ['Heat produced relative to fuel consumed and Heat eff', 27]
    m.addConstrs((unit_prod['Heat',d,h] == (
        unit_cons['Biogas',d,h] + unit_cons['Gas',d,h] + unit_cons['BM',d,h])*
                  (1 - P[c,'Eff_elec'])*P[c,'Eff_thermal'] for d in Days for h in Hours), n);    
    
    n = 'ICE_size'
    C_meta[n] = ['Upper limit on Elec produced relative to installed capacity', 28]
    m.addConstrs((unit_prod['Elec',d,h] <= unit_size for d in Days for h in Hours), n);
 


###############################################################################
### Anaerobic Digester - Energy conversion
###############################################################################


def ad(m, Days, Hours, unit_prod, unit_cons, unit_size, AD_cons_Heat, unit_install, P):
    """ MILP model of an AD with constant efficiency. Startup time is neglected.
        The AD consumes all biomass available if installed. The heat load profile
        pre-calculated.
    """
    c = 'AD'  
    n = 'AD_biogas_prod'
    C_meta[n] = ['Biogas produced relative to Biomass cons and Efficiency', 29]
    m.addConstrs((unit_prod['Biogas',d,h] == unit_cons['Biomass',d,h]*P[c,'Eff']
                  for d in Days for h in Hours), n);
    
    n = 'AD_biomass_cons'
    C_meta[n] = ['Biomass consumed equivalent to all available biomass', 30]
    m.addConstrs((unit_cons['Biomass',d,h] == P['Farm','Biomass_prod']*unit_install
                  for d in Days for h in Hours), n);
    
    n = 'AD_elec_cons'
    C_meta[n] = ['Elec cons relative to Biogas produced', 31]
    m.addConstrs((unit_cons['Elec',d,h] == unit_prod['Biogas',d,h]*P[c,'Elec_cons']
                  for d in Days for h in Hours), n);
    
    n = 'AD_heat_cons'
    C_meta[n] = ['Heat consumed relative to AD size', 32]
    m.addConstrs((unit_cons['Heat',d,h] == AD_cons_Heat[d,h]*unit_install
                  for d in Days for h in Hours), n);
    
    n = 'AD_size'
    C_meta[n] = ['Upper limit on BG prod relative to Installed capacity', 33]
    m.addConstrs((unit_prod['Biogas',d,h] <= unit_size for d in Days for h in Hours), n);  
    
    
    
###############################################################################
### Photovoltaïc  - Energy conversion
###############################################################################


def pv(m, Days, Hours, unit_prod, unit_size, Irradiance, P):
    """ LP model of PV panels. The low efficiency account for sub optimal
        orientation. """
    u = 'PV'
    n = 'PV_production'
    C_meta[n] = ['Elec produced relative to Irradiance eff and surface', 34]
    m.addConstrs((unit_prod['Elec',d,h] == Irradiance[d,h]*P[u,'Eff']*unit_size/
                  P[u,'P_density'] for d in Days for h in Hours), n);
    
    n = 'PV_roof_size'
    C_meta[n] = ['Upper limit on Capacity relative to Available area', 35]
    m.addConstr(unit_size <= P[u,'P_density']*P['Farm','Ground_area']*P[u,'max_utilisation'], n);    



###############################################################################
### Battery - Storage
###############################################################################


def bat(m, Periods, Days, Hours, 
        unit_prod, unit_cons, unit_size, unit_SOC, unit_charge, unit_discharge,
        unit_install, P):
    """ MILP model of a battery
        Charge and discharge efficiency follows Dirk Lauinge MA thesis
    """
    
    # Parameters
    u = 'BAT'
    r = 'Elec'
    Eff = P[u,'Eff']**0.5

    # Constraints
    n = f'{u}_SOC'
    C_meta[n] = ['State of Charge detla relative to prod and cons Elec and eff', 36]
    m.addConstrs((unit_SOC[p+1] - (1 - P[u,'Self_discharge'])*unit_SOC[p] ==  
                  (Eff*unit_cons[t(r,p)] - (1/Eff)*unit_prod[t(r,p)]) 
                  for p in Periods), n);
    
    n = f'{u}_annual_cycle'
    C_meta[n] = ['Cycling constraint on the battery over a year', 37]
    m.addConstr((unit_SOC[0] == unit_SOC[Periods[-1]]), n);
    n = f'{u}_charge_discharge'
    C_meta[n] = ['Prevent the unit from simulateneously charging and discharging', 38]
    m.addConstrs((unit_charge[d,h] + unit_discharge[d,h] <= 1 
                  for d in Days for h in Hours), n);
    n = f'{u}_charge'
    C_meta[n] = ['M constraint to link IS Charging with Elec consumption', 39]
    m.addConstrs((unit_charge[d,h]*Bound >= unit_cons[r,d,h] 
                  for d in Days for h in Hours), n);
    n = f'{u}_discharge'
    C_meta[n] = ['M constraint to link IS Discharging with Elec production', 40]
    m.addConstrs((unit_discharge[d,h]*Bound >= unit_prod[r,d,h] 
                  for d in Days for h in Hours), n);
    
    n = f'{u}_size_SOC'
    C_meta[n] = ['Upper limit on the SOC relative to the Installed Capacity', 41]
    m.addConstrs((unit_SOC[p] <= unit_size for p in Periods), n);
    n = f'{u}_size_discharge'
    C_meta[n] = ['Upper limit on Elec produced to 1 C rate', 42]
    m.addConstrs((unit_prod[r,d,h] <= unit_size for d in Days for h in Hours), n);
    n = f'{u}_size_charge'
    C_meta[n] = ['Upper limit on Elec consumed to 1 C rate', 43]
    m.addConstrs((unit_cons[r,d,h] <= unit_size for d in Days for h in Hours), n);
   
    
    
###############################################################################
### Compressed Gas Tank - Storage
###############################################################################
    

def cgt(m, Periods, Days, Hours, 
        unit_prod, unit_cons, unit_size, unit_SOC, unit_charge, unit_discharge,
        unit_install, P):
    """ MILP model of Compressed Gas Tank for storing Natural Gas. No losses are modeled.
        The tank only accepts Biogas and assumes the energy consumption and volume takeup
        to be equivalent between 1m^3 of Methane and 1m^3 of CO2
    """
    
    u = 'CGT'
    r = 'BM'
    
    # Constraints
    n = f'{u}_SOC'
    C_meta[n] = ['State of Charge detla relative to Produced and Consumed Gas', 44]
    m.addConstrs((unit_SOC[p + 1] - unit_SOC[p] == (unit_cons[t(r,p)] - unit_prod[t(r,p)])
                  for p in Periods), n);
    n = f'{u}_Compression_Elec'
    C_meta[n] = ['Electricity requiered to compress the Gas', 45]
    m.addConstrs((unit_cons['Elec',d,h] == unit_cons[r,d,h]*P[u]['Elec_comp'] 
                  for d in Days for h in Hours), n);
    
    n = f'{u}_annual_cycle'
    C_meta[n] = ['Cycling constraint over a year', 37]
    m.addConstr((unit_SOC[0] == unit_SOC[Periods[-1]]), n);
    n = f'{u}_charge_discharge'
    C_meta[n] = ['Prevent the unit from simulateneously charging and discharging', 38]
    m.addConstrs((unit_charge[d,h] + unit_discharge[d,h] <= 1 
                  for d in Days for h in Hours), n);
    n = f'{u}_charge'
    C_meta[n] = ['M constraint to link IS Charging with BM consumption', 39]
    m.addConstrs((unit_charge[d,h]*Bound >= unit_cons[r,d,h] 
                  for d in Days for h in Hours), n);
    n = f'{u}_discharge'
    C_meta[n] = ['M constraint to link IS Discharging with BM production', 40]
    m.addConstrs((unit_discharge[d,h]*Bound >= unit_prod[r,d,h] 
                  for d in Days for h in Hours), n);
    
    n = f'{u}_size_SOC'
    C_meta[n] = ['Upper limit on the SOC relative to the Installed Capacity', 41]
    m.addConstrs((unit_SOC[p] <= unit_size for p in Periods), n);
    n = f'{u}_size_discharge'
    C_meta[n] = ['Upper limit on discharging rate', 42]
    m.addConstrs((unit_prod[r,d,h] <= unit_size for d in Days for h in Hours), n);
    n = f'{u}_size_charge'
    C_meta[n] = ['Upper limit on charging rate', 43]
    m.addConstrs((unit_cons[r,d,h] <= unit_size for d in Days for h in Hours), n);
   

###############################################################################
### Biogas Storage - Storage
###############################################################################
    

def bs(m, Periods, Days, Hours, 
        unit_prod, unit_cons, unit_size, unit_SOC, unit_charge, unit_discharge, 
        unit_install, P):
    """ MILP model of Biogas Storage for storing raw biogas. The biogas is 
        stored close to atmospheric pressure in an expandable vessel. 1% loss 
        of stored biogas per day.
    """
    
    u = 'BS'
    r = 'Biogas'
    
    # Constraints
    n = f'{u}_SOC'
    C_meta[n] = ['State of Charge detla relative to Produced and Consumed Gas', 46]
    m.addConstrs((unit_SOC[p + 1] - (1 - P[u,'Self_discharge'])*unit_SOC[p] == 
                  (unit_cons[t(r,p)] - unit_prod[t(r,p)]) for p in Periods), n);
    n = f'{u}_Fan_Elec'
    C_meta[n] = ['Electricity requiered to inflate the storage ballon', 47]
    m.addConstrs((unit_cons['Elec',d,h] == 1e-3 * P[u]['Elec_fan'] * unit_size
                  for d in Days for h in Hours), n);
    
    n = f'{u}_annual_cycle'
    C_meta[n] = ['Cycling constraint over a year', 37]
    m.addConstr((unit_SOC[0] == unit_SOC[Periods[-1]]), n);
    n = f'{u}_charge_discharge'
    C_meta[n] = ['Prevent the unit from simulateneously charging and discharging', 38]
    m.addConstrs((unit_charge[d,h] + unit_discharge[d,h] <= 1 
                  for d in Days for h in Hours), n);
    n = f'{u}_charge'
    C_meta[n] = ['M constraint to link IS Charging with BM consumption', 39]
    m.addConstrs((unit_charge[d,h]*Bound >= unit_cons[r,d,h] 
                  for d in Days for h in Hours), n);
    n = f'{u}_discharge'
    C_meta[n] = ['M constraint to link IS Discharging with BM production', 40]
    m.addConstrs((unit_discharge[d,h]*Bound >= unit_prod[r,d,h] 
                  for d in Days for h in Hours), n);
    
    n = f'{u}_size_SOC'
    C_meta[n] = ['Upper limit on the SOC relative to the Installed Capacity', 41]
    m.addConstrs((unit_SOC[p] <= unit_size for p in Periods), n);
    n = f'{u}_size_discharge'
    C_meta[n] = ['Upper limit on discharging rate', 42]
    m.addConstrs((unit_prod[r,d,h] <= unit_size for d in Days for h in Hours), n);
    n = f'{u}_size_charge'
    C_meta[n] = ['Upper limit on charging rate', 43]
    m.addConstrs((unit_cons[r,d,h] <= unit_size for d in Days for h in Hours), n);
    
    
    
###############################################################################
### Biogas cleaning for SOFC - Utility
###############################################################################

def gcsofc(m, Days, Hours, unit_prod, unit_cons, unit_size, P):
    """ MILP model of a Gas Cleaning installation for SOFC applications. The
        installation is a stack of filters to be replaced regularly, losses
        represent the electricity consumed by the fan and the chiller (drying).
    """
    x_BG = P['Physical','Biogas_CH4'] 
    
    u = 'GCSOFC'
    n = f'{u}_production'
    C_meta[n] = ['Biogas prod relative to Biogas cons', 48]
    m.addConstrs((unit_prod[r,d,h] == unit_cons[r,d,h] 
                  for r in ['Biogas', 'BM'] for d in Days for h in Hours), n);
    
    n = f'{u}_Elec_cons'
    C_meta[n] = ['Electricity consumption relative to Biogas production', 49]
    m.addConstrs((unit_cons['Elec',d,h] == P[u,'Elec_cons']*
                  (unit_prod['Biogas',d,h] + unit_prod['BM',d,h]*x_BG)
                  for d in Days for h in Hours), n);
    
    n = f'{u}_size'
    C_meta[n] = ['Upper limit on prod relative to installed capacity', 50]
    m.addConstrs((unit_prod['Biogas',d,h] + unit_prod['BM',d,h]*x_BG
                  <= unit_size for d in Days for h in Hours), n);



###############################################################################
### Biogas Upgrading - Utility
###############################################################################

def bu(m, Days, Hours, unit_prod, unit_cons, unit_size, P):
    """ LP model of a Biogas Upgrading system using membranes. Product has a 95
        to 99% methane content and is called biomethane (BM). Electricity is
        consumed for compression. Most of the metahen is recodevers (some losses)
    """
    u = 'BU'
    
    n = f'{u}_production'
    C_meta[n] = ['Biogas prod relative to Biogas cons', 51]
    m.addConstrs((unit_prod['BM',d,h] == P[u,'Eff']*unit_cons['Biogas',d,h] 
                  for d in Days for h in Hours), n);
    
    n = f'{u}_Elec_cons'
    C_meta[n] = ['Electricity consumption relative to Biogas production', 52]
    m.addConstrs((unit_cons['Elec',d,h] == P[u,'Elec_comp']*unit_prod['BM',d,h]
                  for d in Days for h in Hours), n);
    
    n = f'{u}_size'
    C_meta[n] = ['Upper limit on prod relative to installed capacity', 53]
    m.addConstrs((unit_prod['BM',d,h] <= unit_size for d in Days for h in Hours), n);
    
    
    
###############################################################################
### Gas Fueling Station - Utility
###############################################################################


def gfs(m, Days, Hours, unit_prod, unit_cons, unit_size, U_prod, P):
    """ MILP model of Gas Fueling Station for the slow refueling of utility
        vehicles. Takes Natural Gas or Biomethane as inputs. No gas is stored.
        The gas is dried and compressed to 3600 PSI. The vehicles are refueld
        overnight once a day.
    """
    u = 'GFS'
    Elec_gfs = P[u]['Elec_comp'] + P[u]['Elec_dry']*P['Physical']['Biogas_CH4']

    for r in U_prod:
        n = f'{u}_{r}_production'
        C_meta[n] = [f'{r} prod relative to {r} cons', 54]
        m.addConstrs((unit_prod[r,d,h] == unit_cons[r,d,h] 
                      for d in Days for h in Hours), n);

    n = f'{u}_Comp_Dry_Elec'
    C_meta[n] = ['Electricity requiered to compress and dry the Gas', 55]
    m.addConstrs((unit_cons['Elec',d,h] == 
                  sum(unit_cons[r,d,h]*Elec_gfs for r in U_prod) 
                  for d in Days for h in Hours), n);
    
    n = f'{u}_size'
    C_meta[n] = ['Upper limit on prod relative to installed capacity', 56]
    m.addConstrs((sum(unit_prod[r,d,h] for r in U_prod) <= unit_size 
                  for d in Days for h in Hours), n);    
    
    
###############################################################################
### Grid Injection (of biomethane) - Utility
###############################################################################

def gi(m, Days, Hours, unit_prod, unit_cons, unit_size, P):
    """ LP model of a biomethane grid injection system. For injection into the
        swiss distribution grid (5 bar). The biomethane from the upgrading unit
        is already at 5 to 7 bar. No further compression is considered.
    """
    u = 'GI'
    n = f'{u}_production'
    C_meta[n] = ['BM prod relative to BM cons', 57]
    m.addConstrs((unit_prod['BM',d,h] == unit_cons['BM',d,h] 
                  for d in Days for h in Hours), n);
    
    n = f'{u}_size'
    C_meta[n] = ['Upper limit on prod relative to installed capacity', 58]
    m.addConstrs((unit_prod['BM',d,h] <= unit_size 
                  for d in Days for h in Hours), n);
    
###############################################################################
### END
###############################################################################






