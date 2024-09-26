

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')  # Replace with the appropriate backend
import matplotlib.pyplot as plt

import pypsa
import random

CO2_ocgt= .651 #ton/MWh
CO2_ccgt= .394
CO2_coal= .937
CO2_oil = .935

def mef_log(idx, values, mef, es_energy, gen_update):


    if es_energy.iloc[idx] == 0:
        mef.append(0)
    else:
        # if 'Hard coal' in values.iloc[idx]:
        #     a = 1
        # else:
        #     values['Hard coal'].iloc[idx] = 0

        if values['Hard coal'].iloc[idx]> es_energy.iloc[idx]:
            mef.append(CO2_coal)
            gen_update['Hard coal'].iloc[idx] -= es_energy.iloc[idx]
        else:

            if values['Oil'].iloc[idx] > es_energy.iloc[idx] - values['Hard coal'].iloc[idx]:
                co2_tem = (CO2_oil * (es_energy.iloc[idx] - values['Hard coal'].iloc[idx])+CO2_coal*values['Hard coal'].iloc[idx])/es_energy.iloc[idx]
                mef.append(co2_tem)
                gen_update['Oil'].iloc[idx] = gen_update['Oil'].iloc[idx] - (es_energy.iloc[idx] - gen_update['Hard coal'].iloc[idx])
                gen_update['Hard coal'].iloc[idx] = 0

            else:
                # if 'SCGT' in values.iloc[idx]:
                #     a = 1
                # else:
                #     values['SCGT'].iloc[idx] = 0
                if values['SCGT'].iloc[idx] > es_energy.iloc[idx] - values['Oil'].iloc[idx] - values['Hard coal'].iloc[idx]:
                    co2_tem = (CO2_ocgt * (es_energy.iloc[idx] - values['Oil'].iloc[idx] - values['Hard coal'].iloc[idx]) +
                               CO2_oil * values['Oil'].iloc[idx] + CO2_coal * values['Hard coal'].iloc[idx]) / es_energy.iloc[idx]
                    mef.append(co2_tem)
                    gen_update['SCGT'].iloc[idx] = gen_update['SCGT'].iloc[idx] - (es_energy.iloc[idx] - gen_update['Hard coal'].iloc[idx] - gen_update['Oil'].iloc[idx])
                    gen_update['Hard coal'].iloc[idx] = 0
                    gen_update['Oil'].iloc[idx] = 0

                else:
                    # if ('CCGT' in values.iloc[idx]):
                    #     a = 1
                    # else:
                    #     values['CCGT'].iloc[idx] = 0
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

    return mef, gen_update



def cycle_analysis(charg_x, charg_y, df_gen_0, df_battery_links, df_gen_update):
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
            mef, df_gen_update = mef_log(idx, df_gen_0, mef, df_battery_links, df_gen_update)
            # print(df_gen.iloc[idx]['Hard coal'])
            energy_charge += df_battery_links.iloc[idx]

        co2_charge_cycle.append(np.array(mef).mean())
        energy_charge_cycle.append(energy_charge)
    return co2_charge_cycle, energy_charge_cycle, df_gen_update
