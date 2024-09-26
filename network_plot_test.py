import pypsa
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

pre_dic = '../results_min_ff/old_results/'

network = pypsa.Network(pre_dic+'network_ff.nc')

# print(network.lines)
print(network.links.index)

# network.links = network.links['INTFR', 'INTNED', 'INTEW', 'INTNEM', 'INTIFA2', 'INTNSL', 'INTELEC']
# print(network.branch_components)

print(network.links[network.links.index == 'INTFR'])
#
# fig, ax = plt.subplots(
#     1, 1, subplot_kw={"projection": ccrs.EqualEarth()}, figsize=(8, 8)
# )

load_distribution = (
    network.loads_t.p_set.loc[network.snapshots[0]].groupby(network.loads.bus).sum()
)
network.plot(bus_sizes=1e-5 * load_distribution, branch_components={'Line'}, title="Load distribution")

plt.show()