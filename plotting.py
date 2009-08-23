#!/usr/bin/python
# Copyright 2009 Alex Zvoleff
#
# This file is part of the ChitwanABM agent-based model.
# 
# ChitwanABM is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# ChitwanABM is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# ChitwanABM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact Alex Zvoleff in the Department of Geography at San Diego State 
# University with any comments or questions. See the README.txt file for 
# contact information.

"""
Plot basic statistics on a model run: From a set of model output files, 
plots basic statistics summarizing the model run.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import sys
import os
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
    in_file.close()
    return results

def make_results_list(root_dir, model_IDs=None):
    objects = os.listdir(root_dir)
    # Pull out directories from objects
    dirs = []
    for object in objects:
        if not os.path.isdir(os.path.join(root_dir, object)):
            continue
        model_ID = os.path.basename(object)
        if model_IDs == None or model_ID in model_IDs:
            dirs.append(object)
    results_list = []
    for dir in dirs:
        try:
            new_results = load_results(os.path.join(root_dir, dir, "results.P"))
            results_list.append(new_results)
        except IOError:
            print "warning: no results file found in %s"%(dir)
    return results_list

def plot_pop_stats(results, plot_file, plot_type="raw_data"):
    time = results.get_timesteps()

    num_persons = np.array(results.get_num_persons()) # Final populations for each time step.
    births = np.array(results.get_num_births())
    deaths = np.array(results.get_num_deaths())
    marr = np.array(results.get_num_marriages())
    migr = np.array(results.get_num_migrations())

    if plot_type=="raw_data":
        #events = [births, deaths, marr, migr]
        #labels = ["Births", "Deaths", "Marriages", "Migrations"]
        events = [births, deaths, marr]
        labels = ["Births", "Deaths", "Marriages"]
        yaxis2label = "Events (per  month)"
    elif plot_type=="rates":
        #events = [births/num_persons, deaths/num_persons, marr/num_persons, migr]
        #labels = ["Crude birth rate", "Crude death rate", "Crude marriage rate", "Crude migration rate"]
        events = [births/(num_persons/1000.), deaths/(num_persons/1000.), marr/(num_persons/1000.)]
        labels = ["Crude birth rate", "Crude death rate", "Crude marriage rate"]
        yaxis2label = "Events (per  1000 people / month)"

    plt.figure()
    plt.clf()

    # Plot the population vs time
    plt.plot(time, num_persons, color='k', linewidth=2, linestyle='-', label="Population")
    plt.ylabel("Population")

    # Setup the second axis (sharing the x-axis).
    axR = plt.twinx()
    axR.yaxis.tick_right()
    axR.yaxis.set_label_position("right")
    
    # Now plot births, deaths, and migrations, vs time.
    colors = ['#ff6c01', '#00cd00', 'b', 'k']
    linewidths = [.75, .75, .75, .75]
    #linestyles = ['-', '--', '-.', ':']
    linestyles = ['-', '-', '-', '-']
    for event, color, linewidth, linestyle, label in zip(events, colors, linewidths, linestyles, labels):
        plt.plot(time, event, color=color, linewidth=linewidth, linestyle=linestyle, label=label)

    model_run_ID = results.get_model_run_ID()
    plot_title = "Model run statistics for %s"%(model_run_ID)
    #plt.title(plot_title)
    plt.annotate(model_run_ID, (.93,-.165), xycoords='axes fraction')
    plt.legend(loc='upper left')
    plt.xlabel("Year")
    plt.ylabel(yaxis2label, rotation=270)
    set_tick_labels(time)
    plt.savefig(plot_file)
    plt.clf()

def shaded_plot_pop_stats(results_list, plot_file, plot_type="raw_data"):
    """Make a shaded plot of pop stats that includes 2 standard deviations error 
    bars (as shaded regions around each line)."""
    time = results_list[0].get_timesteps()

    for results in results_list:
        assert results.get_timesteps() == time, "timesteps must be identical for all results"

    num_persons_array = [np.array(result.get_num_persons(), dtype='float') for result in results_list]
    num_persons_array = np.array(num_persons_array)
    births_array = [np.array(result.get_num_births(),
        dtype='float') for result in results_list]
    births_array = np.array(births_array)
    deaths_array = [np.array(result.get_num_deaths(),
        dtype='float') for result in results_list]
    deaths_array = np.array(deaths_array)
    marr_array = [np.array(result.get_num_marriages(),
        dtype='float') for result in results_list]
    marr_array = np.array(marr_array)
    migr_array = [np.array(result.get_num_migrations(),
        dtype='float') for result in results_list]
    migr_array = np.array(migr_array)

    if plot_type=="raw_data":
        #events = [births_array, deaths_array, marr_array, migr_array]
        #labels = ["Births", "Deaths", "Marriages", "Migrations"]
        events = [births_array, deaths_array, marr_array]
        labels = ["Births", "Deaths", "Marriages"]
        yaxis2label = "Events (per  month)"
    elif plot_type=="rates":
        #events = [births_array/num_persons_array,
        #        deaths_array/num_persons_array, marr_array/num_persons_array,
        #        migr_array/num_persons_array]
        #labels = ["Crude birth rate", "Crude death rate", "Crude marriage rate", "Crude migration rate"]
        events = [births_array, deaths_array, marr_array]
        # Convert events per month to events per 1000 people per month
        for outer in xrange(np.shape(events)[0]):
            for inner in xrange(np.shape(events[outer])[0]):
                events[outer][inner] = events[outer][inner] / (num_persons_array[inner]/1000.)
        labels = ["Crude birth rate", "Crude death rate", "Crude marriage rate"]
        yaxis2label = "Events (per  1000 people / month)"

    plt.figure()
    plt.clf()

    # Plot the population vs time
    mean_persons = num_persons_array.mean(0)
    std_persons = num_persons_array.std(0)
    plt.plot(time, mean_persons, color='k', linewidth=2, linestyle='-', label="Population")
    plt.fill_between(time, mean_persons-(std_persons*2), mean_persons+(std_persons*2), color='k', linewidth=0, alpha=.5)
    plt.ylabel("Population")

    # Setup the second axis (sharing the x-axis).
    axR = plt.twinx()
    axR.yaxis.tick_right()
    axR.yaxis.set_label_position("right")
    
    # Now plot births, deaths, and migrations, vs time.
    colors = ['#ff6c01', '#00cd00', 'b', 'k']
    linewidths = [.75, .75, .75, .75]
    #linestyles = ['-', '--', '-.', ':']
    linestyles = ['-', '-', '-', '-']
    for event, color, linewidth, linestyle, label in zip(events, colors, linewidths, linestyles, labels):
        mean = event.mean(0)
        std = event.std(0)
        plt.plot(time, mean, color=color, linewidth=linewidth, linestyle=linestyle, label=label)
        plt.fill_between(time, mean-(std*2), mean+(std*2), color=color, linewidth=0, alpha=.5)

    #plot_title = "Model run statistics for %s model runs"%(len(results_list))
    #plt.title(plot_title)
    annotation = "%s model runs"%(len(results_list))
    plt.annotate(annotation, (1.14,-.165), xycoords='axes fraction', horizontalalignment="right")
    plt.legend(loc='upper left')
    plt.xlabel("Year")
    plt.ylabel(yaxis2label, rotation=270)
    set_tick_labels(time)
    plt.savefig(plot_file)
    plt.clf()

def set_tick_labels(time):
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

if __name__ == "__main__":
    sys.exit(main())
