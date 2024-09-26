import numpy as np
import pandas as pd
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
df_battery_links = pd.read_csv(pre_dic+'links_p_results.csv')
df_gen_bus = pd.read_csv(pre_dic+'buses_p_results.csv')


print(network.lines.columns.to_list())

for region_i in regions:
    region_gen_p = (network.generators_t.p.groupby(network.generators.bus, axis=1).get_group(region_i))
    region_gen_p_carrier =region_gen_p.groupby(network.generators.carrier, axis=1).sum()

    # region_demand = (network.loads_t.p.groupby(network.generators.bus, axis=1).get_group(region_i))
    region_gen_p_carrier['demand'] = network.loads_t.p[region_i]

    # print(region_gen_p)
    file_name = region_i +'_carrier.csv'

    region_gen_p_carrier.to_csv(file_name,header=True)

battery_bus = [s + '_Battery' for s in regions]
df['soc'] = df['Battery']/df['Battery'].max()


battery_charger = [s + '_charger' for s in battery_bus]
battery_discharger = [s + '_discharger' for s in battery_bus]

df_battery_links[battery_discharger]=-df_battery_links[battery_discharger]

# print(df_links_ffmin)
df_battery_links['bus_charger'] = df_battery_links[battery_charger].sum(axis=1)
df_battery_links['bus_discharger'] = df_battery_links[battery_discharger].sum(axis=1)

fig, ax1 = plt.subplots()
df.plot(y='soc',ax=ax1)
battery_soc=[]

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

charg_x, charg_y,  charg_xy = charge_count(df['soc'])


fig, ax = plt.subplots()
# ax.scatter(np.arange(0,len(charg_x),1),charg_xy)
ax.hist(charg_xy, int(len(charg_xy)))

CO2_ocgt= .651 #ton/MWh
CO2_ccgt= .394
CO2_coal= .937
CO2_oil = .935

def mef_log(values, mef, es_energy):
    if es_energy == 0:
        mef.append(0)
    else:
        if 'Hard coal' in values:
            a = 1
        else:
            values['Hard coal'] = 0

        if values['Hard coal']> es_energy:
            mef.append(CO2_coal)

        else:
            if 'Oil' in values:
                a = 1
            else:
                values['Oil'] = 0

            if values['Oil'] > es_energy - values['Hard coal']:
                co2_tem = (CO2_oil * (es_energy - values['Hard coal'])+CO2_coal*values['Hard coal'])/es_energy
                mef.append(co2_tem)

            else:
                if 'SCGT' in values:
                    a = 1
                else:
                    values['SCGT'] = 0
                if values['SCGT'] > es_energy - values['Oil'] - values['Hard coal']:
                    co2_tem = (CO2_ocgt * (es_energy - values['Oil'] - values['Hard coal']) +
                               CO2_oil * values['Oil'] + CO2_coal * values['Hard coal']) / es_energy
                    mef.append(co2_tem)

                else:
                    if ('CCGT' in values):
                        a = 1
                    else:
                        values['CCGT'] = 0
                    if values['CCGT'] > es_energy - values['SCGT'] - values['Oil'] - values['Hard coal']:
                        co2_tem = (CO2_ccgt * (es_energy - values['SCGT'] - values['Oil'] - values['Hard coal']) +
                                   CO2_ocgt * values['SCGT']
                                   + CO2_oil * values['Oil']
                                   + CO2_coal * values['Hard coal']) / es_energy
                        mef.append(CO2_ccgt)

                    else:
                        co2_tem = (CO2_ccgt * values['CCGT'] +
                                   CO2_ocgt * values['SCGT']
                                   + CO2_oil * values['Oil']
                                   + CO2_coal * values['Hard coal']) / es_energy
                        mef.append(co2_tem)



def cycle_analysis(charg_x, charg_y, df_gen, df_battery_links):
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
            mef_log(df_gen.iloc[idx], mef, df_battery_links.iloc[idx])
            # print(df_gen.iloc[idx]['Hard coal'])
            energy_charge += df_battery_links.iloc[idx]

        co2_charge_cycle.append(np.array(mef).mean())
        energy_charge_cycle.append(energy_charge)
    return co2_charge_cycle, energy_charge_cycle


co2_charge_cycle, energy_charge_cycle = cycle_analysis(charg_x, charg_y, df_gen, df_battery_links['bus_charger'])


fig, ax_co2 = plt.subplots()
ax_co2.scatter(charg_xy, co2_charge_cycle)

fig, ax_co2_bus = plt.subplots()
# fig, ax_gen_bus = plt.subplots()

len_plot=50
idx_start=(random.randint(0, len(df['soc'])-len_plot))


for i in regions:
    battery_i = i+'_Battery'
    df_capacity[battery_i + '_soc'] = df_capacity[battery_i]/df_capacity[battery_i].max()
    battery_soc.append(battery_i + '_soc')

    file_name = i + '_carrier.csv'
    df_gen_bus_carrier = pd.read_csv(file_name)

    charg_x, charg_y,  charg_xy = charge_count(df_capacity[battery_i + '_soc'])
    co2_charge_cycle, energy_charge_cycle = cycle_analysis(charg_x, charg_y, df_gen_bus_carrier, df_battery_links[battery_i + '_charger'])
    ax_co2_bus.scatter(charg_xy, co2_charge_cycle, label=i)

    fig, ax_gen_bus = plt.subplots()
    df_gen_bus_carrier=df_gen_bus_carrier[idx_start:idx_start+len_plot]

    df_gen_bus_carrier.plot(y='demand',ax=ax_gen_bus, linestyle = 'dashed')
    gen_list = list(set(df_gen_bus_carrier.columns.to_list()) - set(['demand']))

    df_gen_bus_carrier.plot.area(y=gen_list, stacked=True,ax=ax_gen_bus, title=i)


fig, ax2 = plt.subplots()
df_capacity.plot(y=battery_soc,ax=ax2)

ax_co2_bus.legend()

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
line_capacity.plot.bar(y='s_nom_opt', ax=ax_line, title='S_nom')


fig, ax_network = plt.subplots(subplot_kw={"projection":ccrs.PlateCarree()})

network.plot(projection=ccrs.Mercator(), ax=ax_network, branch_components = {'Line'})
ax_network.set_extent([-10, 2, 50, 60])

plt.show()

