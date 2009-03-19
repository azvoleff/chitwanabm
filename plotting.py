#!/usr/bin/env python
"""
Part of Chitwan Valley agent-based model.

Plot basic statistics on a model run: From a set of model output files, 
plots basic statistics summarizing the model run.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import sys
import pickle

import numpy as np
import matplotlib.pyplot as plt

def main(argv=None):
    if argv is None:
        argv = sys.argv

    results_file = argv[1]
    plot_file = argv[2]

    results = load_results(results_file)
    plot_pop_stats(results, plot_file)

def load_results(results_file):
    try:
        in_file = open(results_file, 'r')
    except IOError:
        raise IOError("error loading results file %s"%(results_file))

    results = pickle.load(in_file)

    return results

def plot_pop_stats(results, plot_file):
    time = results.get_timesteps()

    num_persons = results.get_num_persons() # Final populations for each time step.
    births = results.get_num_births()
    deaths = results.get_num_deaths()
    marr = results.get_num_marriages()
    migr = results.get_num_migrations()

    events = [births, deaths, marr, migr]
    labels = ["Births", "Deaths", "Marriages", "Migrations"]

    plt.figure()
    plt.clf()

    # Plot the population vs time
    plt.plot(time, num_persons, color='k', linewidth=2, linestyle='-', label="Population")
    plt.plot(num_persons, time, )
    plt.ylabel("Population")

    # Setup the second axis (sharing the x-axis).
    axR = plt.twinx()
    axR.yaxis.tick_right()
    axR.yaxis.set_label_position("right")
    
    # Now plot births, deaths, and migrations, vs time.
    colors = ['k', '#ff6c01', '#00cd00', 'b']
    linewidths = [.75, .75, .75, .75]
    #linestyles = ['-', '--', '-.', ':']
    linestyles = ['-', '-', '-', '-']
    for event, color, linewidth, linestyle, label in zip(events, colors, linewidths, linestyles, labels):
        plt.plot(time, event, color=color, linewidth=linewidth, linestyle=linestyle, label=label)

    model_run_ID = results.get_model_run_ID()
    plot_title = "Model run statistics for %s"%(model_run_ID)
    #plt.title(plot_title)
    plt.annotate(model_run_ID, (.93,-.165), xycoords='axes fraction')
    plt.legend(loc='lower left')
    plt.xlabel("Year")
    plt.ylabel("Number of events", rotation=270)

    
    # Label first year, last year, and years that end in 0 and 5
    tick_labels = [int(time[0])]
    tick_years = [time[0]]
    for value in time:
        # Remember to handle str -> floating point imprecision
        rounded_value = int(round(value))
        if abs(rounded_value - value) <= .02:
            if (rounded_value%10 == 0) or (rounded_value%5 == 0):
                tick_labels.append(rounded_value)
                tick_years.append(value)
    tick_labels.append(int(time[-1]))
    tick_years.append(time[-1])
    plt.xticks(tick_years, tick_labels)

    plt.savefig(plot_file)
    plt.clf()

if __name__ == "__main__":
    sys.exit(main())
