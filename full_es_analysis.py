import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')  # Replace with the appropriate backend
import matplotlib.pyplot as plt

import pypsa
import random
import cartopy.crs as ccrs

from analysis_functions import cycle_analysis


#plot parameters (only plot a selected snapshot for reading purpose)
len_plot=100
idx_start=(random.randint(0, 8760-len_plot))

regions = ['EN_NorthEast','EN_NorthWest','EN_Yorkshire',
           'EN_EastMidlands','EN_WestMidlands',
           'EN_East','EN_London','EN_SouthEast',
           'EN_SouthWest','EN_Wales','Scotland',
           'NorthernIreland']

pre_dic = 'current_2/'

network = pypsa.Network(pre_dic+'network.nc')
df = pd.read_csv(pre_dic+'store_e_carrier_results.csv')
df_capacity = pd.read_csv(pre_dic+'stores_e_nom_opt.csv')
df_gen = pd.read_csv(pre_dic+'gen_p_carrier_results.csv')
df_storage_links = pd.read_csv(pre_dic+'links_p_results.csv')
df_gen_bus = pd.read_csv(pre_dic+'buses_p_results.csv')

df_gen_update = df_gen
print(network.lines.columns.to_list())
all_carriers = df_gen.columns.to_list()

for region_i in regions:
    region_gen_p = (network.generators_t.p.groupby(network.generators.bus, axis=1).get_group(region_i))
    region_gen_p_carrier =region_gen_p.groupby(network.generators.carrier, axis=1).sum()

    # region_demand = (network.loads_t.p.groupby(network.generators.bus, axis=1).get_group(region_i))
    region_gen_p_carrier['demand'] = network.loads_t.p[region_i]

    # print(region_gen_p)
    file_name = region_i +'_carrier.csv'
    region_gen_p_carrier.to_csv(file_name,header=True)

battery_bus = [s + '_Battery' for s in regions]
ES_bus = [s + '_OtherStorage' for s in regions]
df['soc_batt'] = df['Battery']/df['Battery'].max()
df['soc_ldes'] = df['ES']/df['ES'].max()

battery_charger = [s + '_charger' for s in battery_bus]
battery_discharger = [s + '_discharger' for s in battery_bus]

ES_charger = [s + '_charger' for s in ES_bus]
ES_discharger = [s + '_discharger' for s in ES_bus]


df_storage_links[battery_discharger]=-df_storage_links[battery_discharger]
df_storage_links[ES_discharger]=-df_storage_links[ES_discharger]

# print(df_links_ffmin)
df_storage_links['bus_charger'] = df_storage_links[battery_charger].sum(axis=1)
df_storage_links['bus_discharger'] = df_storage_links[battery_discharger].sum(axis=1)

# print(df_links_ffmin)
df_storage_links['es_bus_charger'] = df_storage_links[ES_charger].sum(axis=1)
df_storage_links['es_bus_discharger'] = df_storage_links[ES_discharger].sum(axis=1)


# fig, ax1 = plt.subplots()

battery_soc=[]
ES_soc=[]

def charge_count(df_soc):
    charg_x = [] #cycle starting idx
    charg_y = [] # cycle ending idx

    zero_point = 0.01 #cycle start and end condition - this may be worth a sensitivity analysis
    zero_con = 1
    for idx, soc_i in enumerate(df_soc):
        if zero_con == 1: #SOC is close to zero
            if soc_i > zero_point:
                zero_con = 0 # SOC is larger than zero and start a charge
                charg_x.append(idx)
        if zero_con == 0:
            if soc_i < zero_point: # SOC back to zero
                zero_con = 1 # a cycle ends
                charg_y.append(idx)

    print('start points....')
    print('the num of the start points is ' + str(len(charg_x)))
    print(charg_x)

    print('end points')
    print('the num of the end points is ' + str(len(charg_y)))
    print(charg_y)

    charg_xy = np.array(charg_y) - np.array(charg_x) #duration of each cycle (end idx - start idx)

    return charg_x, charg_y,  charg_xy

charg_x, charg_y,  charg_xy = charge_count(df['soc_batt'])


fig, ax = plt.subplots()
# ax.scatter(np.arange(0,len(charg_x),1),charg_xy)
ax.hist(charg_xy, int(len(charg_xy)))
ax.set_title('histogram of battery')

CO2_ocgt= .651 #ton/MWh
CO2_ccgt= .394
CO2_coal= .937
CO2_oil = .935



co2_charge_cycle, energy_charge_cycle, df_gen_update = cycle_analysis(charg_x, charg_y, df_gen, df_storage_links['bus_charger'], df_gen_update)

fig_co2, ax_co2 = plt.subplots(3, 1, figsize=(15, 10), gridspec_kw={'hspace': 0.5})


ax_co2[0].scatter(charg_xy, co2_charge_cycle, label='batt')

# df_gen_update_plot=df_gen_update[idx_start:idx_start+len_plot]
# df_gen_update_plot.plot(y=['Hard coal','Oil','SCGT','CCGT'],ax=ax_gen,linestyle='dashed')

charg_x_es, charg_y_es,  charg_xy_es = charge_count(df['soc_ldes'])
co2_charge_cycle_es, energy_charge_cycle_es, df_gen_update = cycle_analysis(charg_x_es, charg_y_es, df_gen_update,df_storage_links['es_bus_charger'],df_gen_update)
ax_co2[0].scatter(charg_xy_es, co2_charge_cycle_es, label='ldes')
ax_co2[0].legend()
ax_co2[0].set_title('national battery on top')
ax_co2[1].set_ylabel('CO2 [ton/MWh]', fontsize=12)

df_gen = pd.read_csv(pre_dic+'gen_p_carrier_results.csv')


charg_x_es, charg_y_es,  charg_xy_es = charge_count(df['soc_ldes'])
co2_charge_cycle_es, energy_charge_cycle_es, df_gen_update = cycle_analysis(charg_x_es, charg_y_es, df_gen, df_storage_links['es_bus_charger'],df_gen_update)
ax_co2[1].scatter(charg_xy_es, co2_charge_cycle_es, label='ldes')


co2_charge_cycle, energy_charge_cycle, df_gen_update = cycle_analysis(charg_x, charg_y, df_gen_update, df_storage_links['bus_charger'], df_gen_update)

ax_co2[1].scatter(charg_xy, co2_charge_cycle, label='batt')

# df_gen_update_plot=df_gen_update[idx_start:idx_start+len_plot]
# df_gen_update_plot.plot(y=['Hard coal','Oil','SCGT','CCGT'],ax=ax_gen,linestyle='dashed')


ax_co2[1].legend()
ax_co2[1].set_title('national ldes on top')
ax_co2[1].set_xlabel('Duration [hours]', fontsize=12)
ax_co2[1].set_ylabel('CO2 [ton/MWh]', fontsize=12)

df.plot(y='soc_batt',ax=ax_co2[2])
df.plot(y='soc_ldes',ax=ax_co2[2])

ax_co2[2].legend()
ax_co2[2].set_title('national soc')
ax_co2[2].set_xlabel('Time [hour]', fontsize=12)
ax_co2[2].set_ylabel('SOC [MWh]', fontsize=12)

# fig_co2.set_title('national es co2')


# fig_bus_batt, ax_co2_bus = plt.subplots()
# fig_bus_ldes, ax_co2_bus_2 = plt.subplots()

fig_bus_batt, ax_co2_bus = plt.subplots(2, 1, figsize=(12, 5), gridspec_kw={'hspace': 0.5})


fig, ax_gen_bus = plt.subplots()

df_store = (network.stores_t.e)
stores = ['Battery', 'OtherStorage']

storage_batt = []
storage_ldes = []


for i in regions:
    fig, ax = plt.subplots(3, 1, figsize=(15, 10), gridspec_kw={'hspace': 0.5})
    for j in stores:
        store_carrier = i + '_' + j
        df_store.plot(y=store_carrier, ax=ax[0])
        ax[0].set_title('Energy storage SOC in MWh')
        ax[0].set_ylabel('SOC [MWh]')
        if j == 'Battery':
            storage_batt.append(df_store[store_carrier].max())
        else:
            storage_ldes.append(df_store[store_carrier].max())


    battery_i = i+'_Battery'
    df_capacity[battery_i + '_soc'] = df_capacity[battery_i]/df_capacity[battery_i].max()
    battery_soc.append(battery_i + '_soc')

    ES_i = i + '_OtherStorage'
    df_capacity[ES_i + '_soc'] = df_capacity[ES_i] / df_capacity[ES_i].max()
    ES_soc.append(ES_i + '_soc')


    file_name = i + '_carrier.csv'
    df_gen_bus_carrier = pd.read_csv(file_name)

    # df_gen_bus_carrier.plot(y=df_gen_bus_carrier.columns.to_list(), ax=ax[2])

    df_gen_bus_carrier = df_gen_bus_carrier.reindex(columns=all_carriers, fill_value=0)
    df_gen_bus_carrier_update = df_gen_bus_carrier

    charg_x, charg_y,  charg_xy = charge_count(df_capacity[battery_i + '_soc'])
    co2_charge_cycle, energy_charge_cycle, df_gen_bus_carrier_update = cycle_analysis(charg_x, charg_y, df_gen_bus_carrier, df_storage_links[battery_i + '_charger'],df_gen_bus_carrier_update)
    ax_co2_bus[0].scatter(charg_xy, co2_charge_cycle, label=i)
    ax_co2_bus[0].set_title('battery')
    ax_co2_bus[0].set_xlabel('Storage Duration [hour]')
    ax_co2_bus[0].set_ylabel('CO2 Emissions [ton/MWh]')
    ax_co2_bus[0].set_xlim(0, 8760)  # Adjust min and max as needed
    ax_co2_bus[0].set_ylim(0, 0.62)  # Adjust min and max as needed



    ax[1].scatter(charg_xy, co2_charge_cycle, label='battery')
    # ax[1].set_title('Battery CO2 Emissions')
    ax[1].set_xlabel('Storage Duration [hour]')
    ax[1].set_ylabel('CO2 Emissions [ton/MWh]')

    # df_storage_links.plot(y= [battery_i + '_charger',battery_i + '_discharger'], ax=ax[2], label=['batt_c','batt_d'])



    charg_x_es, charg_y_es, charg_xy_es = charge_count(df_capacity[ES_i + '_soc'])
    co2_charge_cycle_es, energy_charge_cycle_es, df_gen_bus_carrier_update = cycle_analysis(charg_x_es, charg_y_es,
                                                           df_gen_bus_carrier_update,
                                                           df_storage_links[ES_i + '_charger'],df_gen_bus_carrier_update)

    ax_co2_bus[1].scatter(charg_xy_es, co2_charge_cycle_es, marker='s', label=i)
    print(i)
    print(charg_xy_es, co2_charge_cycle_es)
    ax_co2_bus[1].set_title('LDES')
    ax_co2_bus[1].set_xlabel('Storage Duration [hour]')
    ax_co2_bus[1].set_ylabel('CO2 Emissions [ton/MWh]')
    ax_co2_bus[1].set_xlim(0, 8760)  # Adjust min and max as needed
    ax_co2_bus[1].set_ylim(0, 0.62)  # Adjust min and max as needed


    ax[1].scatter(charg_xy_es, co2_charge_cycle_es, marker='s', label='ldes')
    # df_storage_links.plot(y=[ES_i + '_charger', ES_i + '_discharger'], ax=ax[2],label=['ldes_c','ldes_d'])


    ###
    file_name = i + '_carrier.csv'
    df_gen_bus_carrier = pd.read_csv(file_name)


    df_gen_bus_carrier = df_gen_bus_carrier.reindex(columns=all_carriers, fill_value=0)
    df_gen_bus_carrier_update = df_gen_bus_carrier

    charg_x, charg_y, charg_xy = charge_count(df_capacity[ES_i + '_soc'])
    co2_charge_cycle, energy_charge_cycle, df_gen_bus_carrier_update = cycle_analysis(charg_x, charg_y,
                                                                                      df_gen_bus_carrier,
                                                                                      df_storage_links[
                                                                                          ES_i + '_charger'],
                                                                                      df_gen_bus_carrier_update)

    ax[2].scatter(charg_xy, co2_charge_cycle, marker='s', label='ldes')
    ax[1].scatter(charg_xy, co2_charge_cycle, facecolor='none')
    # ax[2].set_title('LDES CO2 Emissions')
    ax[2].set_xlabel('Storage duration [hour]')
    ax[2].set_ylabel('CO2 Emissions [ton/MWh]')

    # df_storage_links.plot(y= [battery_i + '_charger',battery_i + '_discharger'], ax=ax[2], label=['batt_c','batt_d'])

    charg_x_es, charg_y_es, charg_xy_es = charge_count(df_capacity[battery_i + '_soc'])
    co2_charge_cycle_es, energy_charge_cycle_es, df_gen_bus_carrier_update = cycle_analysis(charg_x_es, charg_y_es,
                                                                                            df_gen_bus_carrier_update,
                                                                                            df_storage_links[
                                                                                                battery_i + '_charger'],
                                                                                            df_gen_bus_carrier_update)

    ax[2].scatter(charg_xy_es, co2_charge_cycle_es, label='battery')
    ax[1].scatter(charg_xy_es, co2_charge_cycle_es, facecolor='none')








    # fig.savefig(i+'_batt_top.jpg', format='jpg', dpi=300)


    # fig, ax_gen_bus = plt.subplots()
    # df_gen_bus_carrier=df_gen_bus_carrier[idx_start:idx_start+len_plot]
    #
    # df_gen_bus_carrier.plot(y='demand',ax=ax_gen_bus, linestyle = 'dashed')
    # gen_list = list(set(df_gen_bus_carrier.columns.to_list()) - set(['demand']))
    #
    # df_gen_bus_carrier.plot.area(y=gen_list, stacked=True,ax=ax_gen_bus, title=i)

#
# # fig, ax2 = plt.subplots()
# # df_capacity.plot(y=battery_soc,ax=ax2)
#
# ax_co2_bus.legend()
# ax_co2_bus_2.legend()
#
# fig_bus_batt.savefig('bus_batt_co2.jpg', format='jpg', dpi=300)
# fig_bus_ldes.savefig('bus_ldes_co2.jpg', format='jpg', dpi=300)
#
# #
fig, ax_line = plt.subplots()
# df_line_0 = (network.lines_t.p0)
# df_line_1 = (network.lines_t.p1)
#
# df_line_0=df_line_0[idx_start:idx_start+len_plot]
# df_line_1=df_line_1[idx_start:idx_start+len_plot]
#
# df_line_0.plot(y=df_line_0.columns.to_list(), ax=ax_line)
# df_line_1.plot(y=df_line_1.columns.to_list(), ax=ax_line)

line_capacity = network.lines
line_capacity.plot.bar(y='s_nom_opt', ax=ax_line)

ax_line.set_xlabel('Regions')  # Replace with the appropriate label
ax_line.set_ylabel('Capacity [MWh]')  # Replace with the appropriate label
ax_line.set_title('Line Capacities')


# fig, ax_stores = plt.subplots()
#
#
# # Create the first set of bars
# ax_stores.bar(regions, storage_batt, label='Battery')
#
# # Create the second set of bars stacked on top of the first set
# ax_stores.bar(regions, storage_ldes, label='LDES')
#
# # Add labels and title
# ax_stores.set_xlabel('Regions')
# ax_stores.set_ylabel('Storage MWh')
# ax_stores.legend()

# Create figure and axes
fig, ax_stores = plt.subplots()

# Create the first set of bars
ax_stores.bar(regions, storage_batt, label='Battery')

# Create the second set of bars stacked on top of the first set
ax_stores.bar(regions, storage_ldes, label='LDES', bottom=storage_batt)

# Set y-axis to log scale
ax_stores.set_yscale('log')

# Add labels and title
ax_stores.set_xlabel('Regions')
ax_stores.set_ylabel('Storage MWh (log scale)')
ax_stores.legend()

# Customize x-axis labels with numbering
x_positions = range(len(regions))
ax_stores.set_xticks(x_positions, x_positions)  # Original labels
# for i, (pos, label) in enumerate(zip(x_positions, regions), start=1):
#     ax_stores.text(pos, 1e2, f'{i}: {label}', ha='center', va='bottom')



plt.show()

