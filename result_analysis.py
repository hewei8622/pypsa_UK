import numpy as np
import pandas as pd
import pypsa
import matplotlib.pyplot as plt

from datetime import timedelta
from datetime import datetime

import random

def read_results(file):
    df = pd.read_csv(file)
    df['time'] = pd.to_datetime(df['snapshot'])
    df = df.set_index('time')
    df.drop(columns='snapshot')
    return df

file_normal_uk_demand = 'UK_old_1/demand_p.csv'
file_normal_uk_gen = 'UK_old_1/gen_p_carrier_results.csv'
# file_normal_uk_bus= 'UK_old_1/buses_p_results.csv'
#
#
df_gen = read_results(file_normal_uk_gen)
df_demand = read_results(file_normal_uk_demand)
df_demand['sum'] = df_demand[df_demand.columns.to_list()].sum(axis = 1)
# df_bus = read_results(file_normal_uk_bus)
#
#
# file_ffmin_uk_demand = '../results_min_ff/demand_p.csv'
# file_ffmin_uk_gen = '../results_min_ff/gen_p_results.csv'
#
# df_gen_ffmin = read_results(file_ffmin_uk_gen)
# df_demand_ffmin = read_results(file_ffmin_uk_demand)
# df_demand_ffmin['sum'] = df_demand_ffmin[df_demand_ffmin.columns.to_list()].sum(axis = 1)


file_ffmin_uk_demand = '../results_min_ff/demand_p.csv'
file_ffmin_uk_gen = '../results_min_ff/gen_p_results.csv'
file_ffmin_uk_gen_carrier = '../results_min_ff/gen_p_carrier_results.csv'

file_ffmin_uk_gen_buses = '../results_min_ff/buses_p_results.csv'
file_ffmin_uk_links = '../results_min_ff/links_p_results.csv'


file_ffmin_uk_store_p_carrier = '../results_min_ff/store_p_carrier_results.csv'
file_ffmin_uk_store_e_carrier = '../results_min_ff/store_e_carrier_results.csv'

file_uk_store_p_carrier = 'UK_old_1/store_p_carrier_results.csv'
file_uk_store_e_carrier = 'UK_old_1/store_e_carrier_results.csv'




df_gen_ffmin = read_results(file_ffmin_uk_gen)
df_demand_ffmin = read_results(file_ffmin_uk_demand)
df_demand_ffmin['sum'] = df_demand_ffmin[df_demand_ffmin.columns.to_list()].sum(axis = 1)

df_gen_carrier = read_results(file_ffmin_uk_gen_carrier)
df_gen_bus = read_results(file_ffmin_uk_gen_buses)

df_links_ffmin = read_results(file_ffmin_uk_links)


df_store_p_carrier = read_results(file_ffmin_uk_store_p_carrier)
df_store_e_carrier = read_results(file_ffmin_uk_store_e_carrier)

df_store_p_carrier_cost = read_results(file_uk_store_p_carrier)
df_store_e_carrier_cost = read_results(file_uk_store_e_carrier)


# df_gen_carrier['batt'] = df_store_p_carrier['Battery']

lc_carriers = ['Nuclear','Hydro','Biomass','Biogas', 'Wind offshore', 'Wind', 'PV', 'Other RES']
ff_carriers = ['Hard coal','Oil','Hydro','CCGT', 'SCGT']
all_carriers = df_gen_carrier.columns.to_list()
others = list(set(all_carriers) - set(lc_carriers) - set(ff_carriers))

regions = ['EN_NorthEast','EN_NorthWest','EN_Yorkshire',
           'EN_EastMidlands','EN_WestMidlands',
           'EN_East','EN_London','EN_SouthEast',
           'EN_SouthWest','EN_Wales','Scotland',
           'NorthernIreland']

phs_bus = ['Dinorwig_HPS','Ffestiniog_HPS',	'Cruachan_HPS',	'Foyers_HPS',	'CoireGlas_HPS']
battery_bus = ['EN_NorthEast_Battery',
               'EN_NorthWest_Battery',
               'EN_Yorkshire_Battery',
               'EN_EastMidlands_Battery',
               'EN_WestMidlands_Battery',
               'EN_East_Battery',
               'EN_London_Battery',
               'EN_SouthEast_Battery',
               'EN_SouthWest_Battery',
               'EN_Wales_Battery',
               'Scotland_Battery',
               'NorthernIreland_Battery']
es_buses = []

battery_charger = [s + '_charger' for s in battery_bus]
battery_discharger = [s + '_discharger' for s in battery_bus]

df_links_ffmin[battery_discharger]=-df_links_ffmin[battery_discharger]

# print(df_links_ffmin)
df_links_ffmin['bus_charger'] = df_links_ffmin[battery_charger].sum(axis=1)
df_links_ffmin['bus_discharger'] = df_links_ffmin[battery_discharger].sum(axis=1)



print(df_links_ffmin['bus_charger'])

len_plot=200
idx_start=(random.randint(0, len(df_gen_ffmin)-len_plot))
#
df_plot_demand_normal=df_demand[idx_start:idx_start+len_plot]
df_plot_gen_normal=df_gen[idx_start:idx_start+len_plot]
# df_plot_bus_normal=df_bus[idx_start:idx_start+len_plot]

df_plot_links_ffmin=df_links_ffmin[idx_start:idx_start+len_plot]


# fig, ax0 =plt.subplots()
# df_plot_bus_normal.plot(y=df_plot_bus_normal.columns.to_list(), ax=ax0)

fig, ax02 = plt.subplots()
df_plot_gen_normal.plot.area(y = ff_carriers, stacked = True, ax=ax02, legend = False)

df_plot_demand_normal.plot(y = 'sum', stacked = True, linestyle = 'dashed', ax=ax02, legend = False, color = 'blue')
ax02.set_title('normal_cost_min')

fig, ax1 = plt.subplots()

df_plot_demand_ffmin = df_demand_ffmin[idx_start:idx_start+len_plot]
df_plot_gen_ffmin = df_gen_carrier[idx_start:idx_start+len_plot]
df_plot_store_p = df_store_p_carrier[idx_start:idx_start+len_plot]
df_plot_store_e = df_store_e_carrier[idx_start:idx_start+len_plot]
df_plot_store_e_cost = df_store_e_carrier_cost[idx_start:idx_start+len_plot]


df_gen_bus = df_gen_bus[idx_start:idx_start+len_plot]


df_plot_gen_ffmin.plot.area(y = ff_carriers, stacked = True, ax=ax1)
df_plot_demand_ffmin.plot(y = 'sum', stacked = True, linestyle = 'dashed', ax=ax1, legend = False, color = 'blue')
ax1.set_title('ff_min')

fig, ax2 = plt.subplots()
df_plot_store_e.plot(y ='Battery', ax=ax2)
df_plot_store_e_cost.plot(y = 'Battery',ax=ax2, linestyle = 'dashed')

# Shrink current axis by 20%
box = ax1.get_position()
ax1.set_position([box.x0, box.y0, box.width*.8, box.height])

# Put a legend to the right of the current axis
ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
ax1.locator_params(axis='x', nbins=3)


fig, ax3 = plt.subplots()
df_links_ffmin.plot(y=battery_charger+battery_discharger, ax=ax3, legend=False)




# CO2_ocgt= 651 #ton/GWh
# CO2_ccgt= 394
# CO2_coal= 937
# #https://www.parliament.uk/documents/post/postpn268.pdf
# CO2_biomass= 120
# CO2_solar= 0
# CO2_wind= 0
# CO2_nuclear= 0
# CO2_hydro= 0
# CO2_otherRES = 0
# CO2_oil = 935

dict_carriers = {
    'Lignite': 0.937, 'Hard coal': 0.937, 'CCGT':.394, 'OCGT':.651, 'Gas': 0.187, 'Gas CCS': 0, 'Oil': 0.935, 'Hydrogen': 0, 'Biomass': 0.403, 'Biogas': 0.178, 'BECCS': 0,
    'Geothermal': 0.026, 'Wind': 0, 'Wind offshore': 0, 'PV': 0, 'HPS': 0, 'Hydro': 0, 'Other RES': 0, 'CBF': 0, 'VOLL': 0, 'Battery': 0, 'Other storage' : 0, 'Nuclear': 0
}

# print(dict_carriers)
# print(dict_carriers['Lignite'])


plt.show()

