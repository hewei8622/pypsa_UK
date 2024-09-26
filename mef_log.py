import numpy as np
import pandas as pd

# Dictionary mapping energy sources to their respective CO2 emission factors (in tons/MWh).
CO2_FACTORS = {
    'Hard coal': 0.937,  # Emission factor for hard coal.
    'Oil': 0.935,        # Emission factor for oil.
    'SCGT': 0.651,       # Emission factor for Single Cycle Gas Turbines.
    'CCGT': 0.394        # Emission factor for Combined Cycle Gas Turbines.
}


def cef_discharge_log(idx, values, cef, df_battery_links_charge):


    if df_battery_links_charge.iloc[idx] == 0:
        cef.append(0)
        return cef

    if values["Hard coal"].iloc[idx] > 0:
        co2 = CO2_FACTORS["Hard coal"]
    else:
        if values["Oil"].iloc[idx] > 0:
            co2 = CO2_FACTORS["Oil"]
        else:
            if values["SCGT"].iloc[idx] > 0:
                co2 = CO2_FACTORS["SCGT"]
            else:
                if values["CCGT"].iloc[idx] > 0:
                    co2 = CO2_FACTORS["CCGT"]
                else:
                    co2 = 0

    emission_discahrged  = co2 * df_battery_links_charge.iloc[idx]
    cef.append(emission_discahrged)
    return cef

def cef_log(idx, values, cef, df_battery_links_charge,gen_update):
    """
    Calculate and append the marginal emission factor (MEF) for a specific index based on the available energy source data.

    Args:
    idx (int): Index for the current time step in the DataFrame.
    values (DataFrame): DataFrame containing the energy generation data for each source.
    mef (list): List to accumulate calculated MEF values.
    es_energy (Series): Series indicating the amount of energy stored or used at each time step.
    gen_update (DataFrame): DataFrame tracking the updated generation data after accounting for storage usage.

    Returns:
    tuple: Returns the updated mef list and gen_update DataFrame after calculations.
    """
    # Append zero to mef list if the energy storage at the current index is zero (no energy use).
    if df_battery_links_charge.iloc[idx] == 0:
        cef.append(0)
        return cef, gen_update

    remaining_energy = df_battery_links_charge.iloc[idx]
    total_emissions = 0

    # Loop through each energy source available in the CO2_FACTORS dictionary.
    for source, co2 in CO2_FACTORS.items():
        if remaining_energy <= 0:
            break

        # Calculate the energy used from the current source without exceeding the remaining energy.
        used_energy = min(values[source].iloc[idx], remaining_energy)
        total_emissions += used_energy * co2  # Accumulate total emissions based on the used energy and its CO2 factor.
        remaining_energy -= used_energy  # Decrease the remaining energy to be distributed.
        gen_update[source].iloc[idx] -= used_energy  # Update the generation data for the current source.

    # Compute the MEF for the current index if there was any energy usage, otherwise set it to zero.

    cef.append(total_emissions)

    return cef, gen_update


def aef_log(idx, values, aef, df_battery_links_charge,gen_update):
    """
    Calculate and append the marginal emission factor (MEF) for a specific index based on the available energy source data.

    Args:
    idx (int): Index for the current time step in the DataFrame.
    values (DataFrame): DataFrame containing the energy generation data for each source.
    mef (list): List to accumulate calculated MEF values.
    es_energy (Series): Series indicating the amount of energy stored or used at each time step.
    gen_update (DataFrame): DataFrame tracking the updated generation data after accounting for storage usage.

    Returns:
    tuple: Returns the updated mef list and gen_update DataFrame after calculations.
    """
    # Append zero to mef list if the energy storage at the current index is zero (no energy use).
    if df_battery_links_charge.iloc[idx] == 0:
        aef.append(0)
        return aef, gen_update

    remaining_energy = df_battery_links_charge.iloc[idx]
    total_emissions = 0

    # Loop through each energy source available in the CO2_FACTORS dictionary.
    for source, co2 in CO2_FACTORS.items():
        # Calculate the energy used from the current source without exceeding the remaining energy.
        total_emissions += values[source].iloc[idx] * co2  # Accumulate total emissions based on the used energy and its CO2 factor.

    #get aef (co2/MWh) then times the charged energy in MWh
    total_emissions = total_emissions * df_battery_links_charge.iloc[idx]/values.iloc[idx].sum()

    # Compute the MEF for the current index if there was any energy usage, otherwise set it to zero.

    aef.append(total_emissions)

    return aef




def mef_log(idx, values, mef, df_battery_links_charge,gen_update):
    """
    Calculate and append the marginal emission factor (MEF) for a specific index based on the available energy source data.

    Args:
    idx (int): Index for the current time step in the DataFrame.
    values (DataFrame): DataFrame containing the energy generation data for each source.
    mef (list): List to accumulate calculated MEF values.
    es_energy (Series): Series indicating the amount of energy stored or used at each time step.
    gen_update (DataFrame): DataFrame tracking the updated generation data after accounting for storage usage.

    Returns:
    tuple: Returns the updated mef list and gen_update DataFrame after calculations.
    """
    # Append zero to mef list if the energy storage at the current index is zero (no energy use).
    if df_battery_links_charge.iloc[idx] == 0:
        mef.append(0)
        return mef, gen_update

    total_emissions = 0

    if values["Hard coal"].iloc[idx]>0:
        co2 = CO2_FACTORS["Hard coal"]
    else:
        if values["Oil"].iloc[idx] > 0:
            co2 = CO2_FACTORS["Oil"]
        else:
            if values["SCGT"].iloc[idx] > 0:
                co2 = CO2_FACTORS["SCGT"]
            else:
                if values["CCGT"].iloc[idx] > 0:
                    co2 = CO2_FACTORS["CCGT"]
                else:
                    co2 = 0

    total_emissions = co2 * df_battery_links_charge.iloc[idx]

    mef.append(total_emissions)

    return mef



def cycle_analysis(charg_x, charg_y, df_gen_0, df_battery_links_charge,df_battery_links_discharge, df_gen_update, es_idx):
    """
    Analyze charging cycles to determine the CO2 impact and energy used per cycle.

    Args:
    charg_x (list): List of start indices for each charging cycle.
    charg_y (list): List of end indices for each charging cycle.
    df_gen_0 (DataFrame): DataFrame containing initial generation data.
    df_battery_links (DataFrame): DataFrame with links to battery usage data.
    df_gen_update (DataFrame): DataFrame to be updated with new generation values after each cycle.

    Returns:
    tuple: Returns lists of CO2 impacts and energy charges per cycle, along with the updated generation DataFrame.
    """
    energy_charge_cycle = []
    energy_discharged_cycle = []
    co2_charge_cycle = []
    emissions_charged = 0
    emissions_discharged = 0
    emissions_charged_cycle = []
    emissions_discharged_cycle = []

    eff=1
    if es_idx==0:
        eff = .9

    if es_idx==1:
        eff = .7

    # Process each charging cycle defined by start and end indices.
    for start, end in zip(charg_x, charg_y):
        # Sum the energy used during the current cycle.
        energy_charge = df_battery_links_charge.iloc[start:end].sum()
        energy_discharge = -df_battery_links_discharge.iloc[start:end].sum()*eff
        cef_charge = []  # Initialize a new list to store MEF values for the current cycle.
        cef_discharge = []

        # Calculate MEF for each index in the current cycle.
        for idx in range(start, end):
            cef_charge, df_gen_update = cef_log(idx, df_gen_0, cef_charge, df_battery_links_charge, df_gen_update)
            cef_discharge = cef_discharge_log(idx, df_gen_update, cef_discharge, -df_battery_links_discharge)

        # Calculate the average MEF for the cycle and append to the co2_charge_cycle list.
        emissions_charged = np.sum(cef_charge)
        emissions_discharged = np.sum(cef_discharge)
        delta_emissions =  - emissions_discharged + emissions_charged
        #if emission discharged < emission_charged, no need to use storage as the marginal generators have lower emissions
        #if emission discharged > emission_charged, using storage can lower emissions

        emissions_charged_cycle.append(emissions_charged)
        emissions_discharged_cycle.append(emissions_discharged)
        co2_charge_cycle.append(delta_emissions/energy_discharge)
        energy_charge_cycle.append(energy_charge)
        energy_discharged_cycle.append(energy_discharge)


    return co2_charge_cycle, energy_charge_cycle, energy_discharged_cycle, emissions_charged_cycle, emissions_discharged_cycle, df_gen_update