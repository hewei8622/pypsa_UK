import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Replace with the appropriate backend
import matplotlib.pyplot as plt

import pypsa
import random
import cartopy.crs as ccrs

regions = ['EN_NorthEast','EN_NorthWest','EN_Yorkshire',
           'EN_EastMidlands','EN_WestMidlands',
           'EN_East','EN_London','EN_SouthEast',
           'EN_SouthWest','EN_Wales','Scotland',
           'NorthernIreland']

pre_dic = '../results_min_ff/2x_current/'
# pre_dic = 'UK_old_1/'
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


fig, ax1 = plt.subplots()
df.plot(y='soc_batt',ax=ax1)
df.plot(y='soc_ldes',ax=ax1)
battery_soc=[]
ES_soc=[]

def charge_count(df_soc):
    charg_x = []
    charg_y = []

    zero_point = 0.01
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

    charg_xy = np.array(charg_y) - np.array(charg_x)

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

def mef_log(idx, values, mef, es_energy, gen_update):

    if es_energy.iloc[idx] == 0:
        mef.append(0)
    else:
        if 'Hard coal' in values.iloc[idx]:
            a = 1
        else:
            values['Hard coal'].iloc[idx] = 0

        if values['Hard coal'].iloc[idx]> es_energy.iloc[idx]:
            mef.append(CO2_coal)
            gen_update['Hard coal'].iloc[idx] -= es_energy.iloc[idx]
        else:
            if 'Oil' in values.iloc[idx]:
                a = 1
            else:
                values['Oil'].iloc[idx] = 0

            if values['Oil'].iloc[idx] > es_energy.iloc[idx] - values['Hard coal'].iloc[idx]:
                co2_tem = (CO2_oil * (es_energy.iloc[idx] - values['Hard coal'].iloc[idx])+CO2_coal*values['Hard coal'].iloc[idx])/es_energy.iloc[idx]
                mef.append(co2_tem)
                gen_update['Oil'].iloc[idx] = gen_update['Oil'].iloc[idx] - (es_energy.iloc[idx] - gen_update['Hard coal'].iloc[idx])
                gen_update['Hard coal'].iloc[idx] = 0

            else:
                if 'SCGT' in values.iloc[idx]:
                    a = 1
                else:
                    values['SCGT'].iloc[idx] = 0
                if values['SCGT'].iloc[idx] > es_energy.iloc[idx] - values['Oil'].iloc[idx] - values['Hard coal'].iloc[idx]:
                    co2_tem = (CO2_ocgt * (es_energy.iloc[idx] - values['Oil'].iloc[idx] - values['Hard coal'].iloc[idx]) +
                               CO2_oil * values['Oil'].iloc[idx] + CO2_coal * values['Hard coal'].iloc[idx]) / es_energy.iloc[idx]
                    mef.append(co2_tem)
                    gen_update['SCGT'].iloc[idx] = gen_update['SCGT'].iloc[idx] - (es_energy.iloc[idx] - gen_update['Hard coal'].iloc[idx] - gen_update['Oil'].iloc[idx])
                    gen_update['Hard coal'].iloc[idx] = 0
                    gen_update['Oil'].iloc[idx] = 0

                else:
                    if ('CCGT' in values.iloc[idx]):
                        a = 1
                    else:
                        values['CCGT'].iloc[idx] = 0
                    if values['CCGT'].iloc[idx] > es_energy.iloc[idx] - values['SCGT'].iloc[idx] - values['Oil'].iloc[idx] - values['Hard coal'].iloc[idx]:
                        co2_tem = (CO2_ccgt * (es_energy.iloc[idx] - values['SCGT'].iloc[idx] - values['Oil'].iloc[idx] - values['Hard coal'].iloc[idx]) +
                                   CO2_ocgt * values['SCGT'].iloc[idx]
                                   + CO2_oil * values['Oil'].iloc[idx]
                                   + CO2_coal * values['Hard coal'].iloc[idx]) / es_energy.iloc[idx]
                        mef.append(co2_tem)
                        gen_update['CCGT'].iloc[idx] = gen_update['CCGT'].iloc[idx] - (
                                    es_energy.iloc[idx] - gen_update['Hard coal'].iloc[idx] - gen_update['Oil'].iloc[idx]- gen_update['SCGT'].iloc[idx])
                        gen_update['Hard coal'].iloc[idx] = 0
                        gen_update['Oil'].iloc[idx] = 0
                        gen_update['SCGT'].iloc[idx] = 0

                    else:
                        co2_tem = (CO2_ccgt * values['CCGT'].iloc[idx] +
                                   CO2_ocgt * values['SCGT'].iloc[idx]
                                   + CO2_oil * values['Oil'].iloc[idx]
                                   + CO2_coal * values['Hard coal'].iloc[idx]) / es_energy.iloc[idx]
                        mef.append(co2_tem)
                        gen_update['Hard coal'].iloc[idx] = 0
                        gen_update['Oil'].iloc[idx] = 0
                        gen_update['SCGT'].iloc[idx] = 0
                        gen_update['CCGT'].iloc[idx] = 0



def cycle_analysis(charg_x, charg_y, df_gen, df_battery_links, df_gen_update):
    energy_charge_cycle = []
    co2_charge_cycle = []
    mef=[]

    for i in np.arange(0, len(charg_x),1):
        idx0 = charg_x[i]
        idx1 = charg_y[i]

        co2_charge = 0
        energy_charge = 0
        mef=[]

        for idx in np.arange(idx0,idx1,1):
            mef_log(idx, df_gen, mef, df_battery_links, df_gen_update)
            # print(df_gen.iloc[idx]['Hard coal'])
            energy_charge += df_battery_links.iloc[idx]

        co2_charge_cycle.append(np.array(mef).mean())
        energy_charge_cycle.append(energy_charge)
    return co2_charge_cycle, energy_charge_cycle



fig_es_nation, ax_co2 = plt.subplots()

charg_x_es, charg_y_es,  charg_xy_es = charge_count(df['soc_ldes'])
co2_charge_cycle_es, energy_charge_cycle_es = cycle_analysis(charg_x_es, charg_y_es, df_gen,df_storage_links['es_bus_charger'],df_gen_update)
ax_co2.scatter(charg_xy_es, co2_charge_cycle_es, label='ldes')

co2_charge_cycle, energy_charge_cycle = cycle_analysis(charg_x, charg_y, df_gen_update, df_storage_links['bus_charger'], df_gen_update)
ax_co2.scatter(charg_xy, co2_charge_cycle, label='batt')

ax_co2.legend()
ax_co2.set_title('national es emission vs duration')
fig_es_nation.savefig('national_co2.jpg', format='jpg', dpi=300)


fig_bus_batt, ax_co2_bus = plt.subplots()
fig_bus_ldes, ax_co2_bus_2 = plt.subplots()

# fig, ax_gen_bus = plt.subplots()

len_plot=50
idx_start=(random.randint(0, len(df['soc_batt'])-len_plot))

df_store = (network.stores_t.e)
stores = ['Battery', 'OtherStorage']

for i in regions:
    fig, ax = plt.subplots(2, 1)
    for j in stores:
        store_carrier = i + '_' + j
        df_store.plot(y=store_carrier, ax=ax[0])

    battery_i = i+'_Battery'
    df_capacity[battery_i + '_soc'] = df_capacity[battery_i]/df_capacity[battery_i].max()
    battery_soc.append(battery_i + '_soc')

    ES_i = i + '_OtherStorage'
    df_capacity[ES_i + '_soc'] = df_capacity[ES_i] / df_capacity[ES_i].max()
    ES_soc.append(ES_i + '_soc')


    file_name = i + '_carrier.csv'
    df_gen_bus_carrier = pd.read_csv(file_name)


    df_gen_bus_carrier = df_gen_bus_carrier.reindex(columns=all_carriers, fill_value=0)
    df_gen_bus_carrier_update = df_gen_bus_carrier


    charg_x_es, charg_y_es, charg_xy_es = charge_count(df_capacity[ES_i + '_soc'])
    co2_charge_cycle_es, energy_charge_cycle_es = cycle_analysis(charg_x_es, charg_y_es,
                                                           df_gen_bus_carrier,
                                                           df_storage_links[ES_i + '_charger'],df_gen_bus_carrier_update)
    ax_co2_bus_2.scatter(charg_xy_es, co2_charge_cycle_es, marker='s', label=i)
    ax_co2_bus_2.set_title('LDES')
    ax[1].scatter(charg_xy_es, co2_charge_cycle_es, marker='s', label='ldes')


    charg_x, charg_y,  charg_xy = charge_count(df_capacity[battery_i + '_soc'])
    co2_charge_cycle, energy_charge_cycle = cycle_analysis(charg_x, charg_y, df_gen_bus_carrier_update, df_storage_links[battery_i + '_charger'],df_gen_bus_carrier_update)
    ax_co2_bus.scatter(charg_xy, co2_charge_cycle, label=i)
    ax_co2_bus.set_title('battery')
    ax[1].scatter(charg_xy, co2_charge_cycle, label='battery')
    fig.savefig(i+'.jpg', format='jpg', dpi=300)


    # fig, ax_gen_bus = plt.subplots()
    # df_gen_bus_carrier=df_gen_bus_carrier[idx_start:idx_start+len_plot]
    #
    # df_gen_bus_carrier.plot(y='demand',ax=ax_gen_bus, linestyle = 'dashed')
    # gen_list = list(set(df_gen_bus_carrier.columns.to_list()) - set(['demand']))
    #
    # df_gen_bus_carrier.plot.area(y=gen_list, stacked=True,ax=ax_gen_bus, title=i)


# fig, ax2 = plt.subplots()
# df_capacity.plot(y=battery_soc,ax=ax2)

ax_co2_bus.legend()
ax_co2_bus_2.legend()

fig_bus_batt.savefig('bus_batt_co2.jpg', format='jpg', dpi=300)
fig_bus_ldes.savefig('bus_ldes_co2.jpg', format='jpg', dpi=300)


#
# fig, ax_line = plt.subplots()
# # df_line_0 = (network.lines_t.p0)
# # df_line_1 = (network.lines_t.p1)
# #
# # df_line_0=df_line_0[idx_start:idx_start+len_plot]
# # df_line_1=df_line_1[idx_start:idx_start+len_plot]
# #
# # df_line_0.plot(y=df_line_0.columns.to_list(), ax=ax_line)
# # df_line_1.plot(y=df_line_1.columns.to_list(), ax=ax_line)
#
# line_capacity = network.lines
# line_capacity.plot.bar(y='s_nom_opt', ax=ax_line)
#
#
# fig, ax_network = plt.subplots(subplot_kw={"projection":ccrs.PlateCarree()})
#
# network.plot(projection=ccrs.Mercator(), ax=ax_network, branch_components = {'Line'})
# ax_network.set_extent([-10, 2, 50, 60])

plt.show()

