import seaborn as sns
import geopandas as gpd
import shapefile as shp
from shapely.geometry import Point
sns.set_style('whitegrid')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.colors import to_hex, to_rgb, CSS4_COLORS, LinearSegmentedColormap, ListedColormap
import matplotlib
matplotlib.use('TkAgg')  # Use any other backend that suits your needs




import numpy as np
import pandas as pd
import pypsa
import cartopy.crs as ccrs

regions = ['EN_NorthEast','EN_NorthWest','EN_Yorkshire',
           'EN_EastMidlands','EN_WestMidlands',
           'EN_East','EN_London','EN_SouthEast',
           'EN_SouthWest','EN_Wales','Scotland',
           'NorthernIreland']

pre_dic = '../results_min_ff/2x_current/'
# pre_dic = 'current_2/'


network = pypsa.Network(pre_dic+'network_ff.nc')


fp = '../geo_plot/NUTS_Level_1_January_2018_FEB_in_the_United_Kingdom_2022_8090221601978784291/NUTS_Level_1_January_2018_FEB_in_the_United_Kingdom.shp'
map_df = gpd.read_file(fp)
map_df.head()

print(map_df.columns.to_list())


crs_epsg = ccrs.epsg("3857")
df_epsg = map_df.to_crs(epsg="3857")

# Generate a figure with two axes, one for CartoPy, one for GeoPandas
fig, axs = plt.subplots(subplot_kw={"projection": crs_epsg}, figsize=(10, 10))

# Make the GeoPandas plot
df_epsg.plot(ax=axs, edgecolor="black")

# fig, ax_network = plt.subplots(subplot_kw={"projection":ccrs.PlateCarree()})

gen = network.generators.assign(g=network.generators_t.p.mean()).groupby(["bus", "carrier"]).g.sum()

line_p = network.lines.s_nom_opt
print(line_p)
# print(network.lines_t.p0)



color_carriers = {
    'Lignite': 0.937, 'CBF':0, 'Hard coal': 0.937, 'CCGT':.394, 'SCGT':.651, 'Gas': 0.187, 'Gas CCS': 0, 'Oil': 0.935, 'Hydrogen': 0, 'Biomass': 0.403, 'Biogas': 0.178, 'BECCS': 0,
    'Geothermal': 0.026, 'Wind': 0, 'Wind offshore': 0, 'DSR': 0, 'PV': 0, 'HPS': 0, 'Hydro': 0, 'Other RES': 0, 'CBF': 0, 'VOLL': 0, 'Battery': 0, 'PHES': 0,'ES' : 0, 'Nuclear': 0
}

print(type(color_carriers))



viridis = plt.get_cmap('viridis')
vals = np.linspace(0, 1, len(color_carriers))
color_list = []
for val in vals:
    color_list.append(to_hex(viridis(val)))

color_dict = {}
i=0
for key in color_carriers:
    color_dict[key] = color_list[i]
    i=i+1

print(color_dict)



# flow = pd.Series(10, index=network.branches().index)
# print(flow)

network.plot(bus_sizes = gen/3e4,
             bus_colors=color_dict,
             ax=axs,line_widths=line_p/1e3,
             branch_components = {'Line'}
             )
axs.set_extent([-10, 2, 50, 60])

# plt.show()
plt.savefig('network_plot_results.png')
