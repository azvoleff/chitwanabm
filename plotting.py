#!/usr/bin/env python
"""
Part of Chitwan Valley agent-based model.

Plot basic statistics on a model run: From a set of model output files, 
plots basic statistics summarizing the model run.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import matplotlib.pyplot at plt

def plot_pop_stats(results, plot_file):
    time = results.get_times()

    censuses = results.get_censuses() # Final populations for each time step.
    births = results.get_times()
    deaths = results.get_times()
    migra = results.get_migrations()

    events = [births, deaths, migra]
    labels = ["Births", "Deaths", "Moves"]

    plt.figure()
    plt.clf()

    # Plot the population vs time
    pylab.plot(time, censuses, color='k', linewidth=1, linestyle='k', label="Population")
    plt.plot(censuses, time, )
    plt.xlabel("Year")
    plt.ylabel("Population")

    # Setup the second axis (sharing the x-axis).
    axR = plt.twinx()
    axR.yaxis.tick_right()
    axR.yaxis.set_label_position("right")
    
    # Now plot births, deaths, and migrations, vs time.
    colors = ['#ff6c01', '#00cd00', 'b']
    linewidths = [1, 1, 1]
    linestyles = ['--', '-.', ':']
    for event, color, linewidth, linestyle, label in zip(events, colors, linewidths, linestyles, labels):
        pylab.plot(time, event, color=color, linewidth=linewidth, linestyle=linestyle, label=label)

    plt.ylabel("Number of events", rotation=270)
    plt.title(plotTitle)
    plt.savefig(plot_file)
    plt.clf()
