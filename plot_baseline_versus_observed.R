#!/usr/bin/env Rscript

require(reshape) # For 'melt' command
require(ggplot2, quietly=TRUE)

WIDTH = 8.33
HEIGHT = 5.53
DPI = 300
theme_update(theme_grey(base_size=18))
update_geom_defaults("line", aes(size=1))

source("calc_NBH_stats.R")

baseline_path <- "/media/Zvoleff_Passport/Data/Nepal/ChitwanABM_runs/Baseline"
baseline_name <- "Baseline"

###############################################################################
# Plot events comparison:

# First load CVFS events data
load("CVFS_monthly_events.Rdata")
CVFS_events <- melt(monthly, id.vars="time_Robj")
names(CVFS_events)[2:3] <- c("Event_type", "events")

# Now load baseline events data
load(paste(baseline_path, "ens_results_pop.Rdata", sep="/"))
baseline_events <- ens_results[c(1, grep("^(marr|births|deaths)", names(ens_results)))]
names(baseline_events)[names(baseline_events) == "time.Robj"] <- "time_Robj"
baseline_events <- melt(baseline_events, id.var="time_Robj")
names(baseline_events)[2:3] <- c("Event_type", "events")

baseline_events <- baseline_events[baseline_events$time_Robj >= "1997-1-1" &
                 baseline_events$time_Robj <= "2006-1-1", ]
CVFS_events <- CVFS_events[CVFS_events$time_Robj >= "1997-1-1" & 
                             CVFS_events$time_Robj <= "2006-1-1", ]

# Make levels in baseline match those in CVFS
baseline_events$Event_type <- gsub('marr', 'marriages', baseline_events$Event_type)

baseline_events$Data_type <- "ABM"
CVFS_events$Data_type <- "CVFS"

baseline_events.means <- baseline_events[grep('mean', baseline_events$Event_type), ]
baseline_events.means$Event_type <- gsub('.mean', '', baseline_events.means$Event_type)
baseline_events.sds <- baseline_events[grep('sd', baseline_events$Event_type), ]
baseline_events.sds$Event_type <- gsub('.sd', '', baseline_events.sds$Event_type)

baseline_events.sds$lim.low <- baseline_events.means$events + 
        2*baseline_events.sds$events
baseline_events.sds$lim.up <- baseline_events.means$events -
        2*baseline_events.sds$events

all_events <- rbind(baseline_events.means, CVFS_events)

p <- ggplot()
p + geom_line(aes(time_Robj, events, colour=Event_type, linetype=Data_type), 
              data=all_events) +
    geom_ribbon(aes(x=time_Robj, ymin=lim.low, ymax=lim.up, fill=Event_type),
                alpha=.2, data=baseline_events.sds) +
    scale_fill_discrete(legend=FALSE) + labs(x="Year", y="Number of Events") +
    scale_color_discrete(name="Event Type",
                         breaks=c("births", "deaths", "marriages"),
                         labels=c("Births", "Deaths", "Marriages")) + 
    scale_linetype_discrete(name="Data_type",
                            breaks=c("ABM", "CVFS"),
                            labels=c("ABM", "Observed"))
ggsave("scenario_versus_observed_events_all.png", width=WIDTH, height=HEIGHT, 
       dpi=DPI)

p <- ggplot()
p + geom_line(aes(time_Robj, events, colour=Event_type, linetype=Data_type), 
              data=all_events[all_events$Event_type=="marriages", ]) +
    geom_ribbon(aes(x=time_Robj, ymin=lim.low, ymax=lim.up, fill=Event_type),
                alpha=.2, 
                data=baseline_events.sds[all_events$Event_type=="marriages", ]) +
    scale_fill_discrete(legend=FALSE) + labs(x="Year", y="Number of Events") +
    scale_color_discrete(name="Event Type",
                         breaks=c("births", "deaths", "marriages"),
                         labels=c("Births", "Deaths", "Marriages")) + 
    scale_linetype_discrete(name="Data_type",
                            breaks=c("ABM", "CVFS"),
                            labels=c("ABM", "Observed"))
ggsave("scenario_versus_observed_events_marriages.png", width=WIDTH, 
       height=HEIGHT, dpi=DPI)

p <- ggplot()
p + geom_line(aes(time_Robj, events, colour=Event_type, linetype=Data_type), 
              data=all_events[all_events$Event_type=="births", ]) +
    geom_ribbon(aes(x=time_Robj, ymin=lim.low, ymax=lim.up, fill=Event_type),
                alpha=.2, 
                data=baseline_events.sds[all_events$Event_type=="births", ]) +
    scale_fill_discrete(legend=FALSE) + labs(x="Year", y="Number of Events") +
    scale_color_discrete(name="Event Type",
                         breaks=c("births", "deaths", "marriages"),
                         labels=c("Births", "Deaths", "Marriages")) + 
    scale_linetype_discrete(name="Data_type",
                            breaks=c("ABM", "CVFS"),
                            labels=c("ABM", "Observed"))
ggsave("scenario_versus_observed_events_births.png", width=WIDTH, 
       height=HEIGHT, dpi=DPI)

p <- ggplot()
p + geom_line(aes(time_Robj, events, colour=Event_type, linetype=Data_type), 
              data=all_events[all_events$Event_type=="deaths", ]) +
    geom_ribbon(aes(x=time_Robj, ymin=lim.low, ymax=lim.up, fill=Event_type),
                alpha=.2, 
                data=baseline_events.sds[all_events$Event_type=="deaths", ]) +
    scale_fill_discrete(legend=FALSE) + labs(x="Year", y="Number of Events") +
    scale_color_discrete(name="Event Type",
                         breaks=c("births", "deaths", "marriages"),
                         labels=c("Births", "Deaths", "Marriages")) + 
    scale_linetype_discrete(name="Data_type",
                            breaks=c("ABM", "CVFS"),
                            labels=c("ABM", "Observed"))
ggsave("scenario_versus_observed_events_deaths.png", width=WIDTH, 
       height=HEIGHT, dpi=DPI)

