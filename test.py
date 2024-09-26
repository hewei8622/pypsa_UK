import matplotlib.pyplot as plt

# Create subplots with adjusted layout
fig, axs = plt.subplots(2, 1, figsize=(8, 8), gridspec_kw={'hspace': 0.5})

# Plot your data or add other content to subplots
axs[0].plot([1, 2, 3], [4, 5, 6], label='Plot 1')
axs[1].plot([1, 2, 3], [6, 5, 4], label='Plot 2')

# Add titles
axs[0].set_title('Title 1', fontsize=14)
axs[1].set_title('Title 2', fontsize=14)



# Show the plot
plt.show()
