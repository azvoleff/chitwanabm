#!/usr/bin/env Rscript

require(reshape) # For 'melt' command
require(ggplot2, quietly=TRUE)

WIDTH = 8.33
HEIGHT = 5.53
DPI = 300
theme_update(theme_grey(base_size=18))
update_geom_defaults("line", aes(size=.5))

source("calc_NBH_stats.R")

baseline_path <- "/media/Zvoleff_Passport/Data/Nepal/ChitwanABM_runs/New_Baseline"
baseline_name <- "Baseline"

load(paste(baseline_path, "ens_results_pop.Rdata", sep="/"))
names(ens_results)[names(ens_results) == "time.Robj"] <- "time_Robj"
ens_results <- ens_results[ens_results$time_Robj >= "1997-2-1" &
                 ens_results$time_Robj <= "2007-7-1", ]

load("/media/truecrypt1/Nepal/CVFS_HHReg/hhreg126.Rdata")

###############################################################################
# Plot events comparison:

# First load CVFS events data
load("CVFS_monthly_events.Rdata")
CVFS_events <- melt(monthly, id.vars="time_Robj")
names(CVFS_events)[2:3] <- c("Event_type", "events")

# Now setup baseline events data
baseline_events <- ens_results[grep("^(time_Robj|marr|births|deaths)", names(ens_results))]
baseline_events <- melt(baseline_events, id.var="time_Robj")
names(baseline_events)[2:3] <- c("Event_type", "events")

CVFS_events <- CVFS_events[CVFS_events$time_Robj >= "1997-2-1" & 
                             CVFS_events$time_Robj <= "2007-7-1", ]

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
p + geom_line(aes(time_Robj, events, linetype=Data_type), 
              data=all_events[all_events$Event_type=="marriages", ]) +
    geom_ribbon(aes(x=time_Robj, ymin=lim.low, ymax=lim.up), alpha=.2, 
                data=baseline_events.sds[all_events$Event_type=="marriages", ]) +
    scale_fill_discrete(legend=FALSE) + labs(x="Year", y="Number of Marriages") +
    scale_linetype_discrete(name="Data_type",
                            breaks=c("ABM", "CVFS"),
                            labels=c("ABM", "Observed"))
ggsave("scenario_versus_observed_events_marriages.png", width=WIDTH, 
       height=HEIGHT, dpi=DPI)

p <- ggplot()
p + geom_line(aes(time_Robj, events, linetype=Data_type), 
              data=all_events[all_events$Event_type=="births", ]) +
    geom_ribbon(aes(x=time_Robj, ymin=lim.low, ymax=lim.up), alpha=.2, 
                data=baseline_events.sds[all_events$Event_type=="births", ]) +
    scale_fill_discrete(legend=FALSE) + labs(x="Year", y="Number of Births") +
    scale_linetype_discrete(name="Data_type",
                            breaks=c("ABM", "CVFS"),
                            labels=c("ABM", "Observed"))
ggsave("scenario_versus_observed_events_births.png", width=WIDTH, 
       height=HEIGHT, dpi=DPI)

p <- ggplot()
p + geom_line(aes(time_Robj, events, linetype=Data_type), 
              data=all_events[all_events$Event_type=="deaths", ]) +
    geom_ribbon(aes(x=time_Robj, ymin=lim.low, ymax=lim.up),
                alpha=.2, 
                data=baseline_events.sds[all_events$Event_type=="deaths", ]) +
    scale_fill_discrete(legend=FALSE) + labs(x="Year", y="Number of Deaths") +
    scale_linetype_discrete(name="Data_type",
                            breaks=c("ABM", "CVFS"),
                            labels=c("ABM", "Observed"))
ggsave("scenario_versus_observed_events_deaths.png", width=WIDTH, 
       height=HEIGHT, dpi=DPI)

# # First calculate ethnicities so we can drop hosueholds of the 'other' # 
# ethnicity.
# ethnic_hhid <- data.frame(ethnic=as.numeric(hhreg$ethnic), hhid=hhreg$hhid108)
# ethnic_hhid <- ethnic_hhid[!is.na(ethnic_hhid$ethnic), ]
# ethnic_hhid <- ethnic_hhid[!is.na(ethnic_hhid$hhid), ]
# ethnic <- aggregate(ethnic_hhid$ethnic, by=list(hhid=ethnic_hhid$hhid), mean, na.rm=TRUE)
# ethnic$x <- round(ethnic$x)
# names(ethnic)[names(ethnic) == 'x'] <- 'ethnic'
# ethnic$ethnic <- factor(ethnic$ethnic, levels=c(1,2,3,4,5), labels=c("UpHindu",
#         "HillTibeto", "LowHindu", "Newar", "TeraiTibeto"))
 
###############################################################################
# Plot population comparison:
load(paste(baseline_path, "ens_results_pop.Rdata", sep="/"))
names(ens_results)[names(ens_results) == "time.Robj"] <- "time_Robj"
ens_results <- ens_results[ens_results$time_Robj >= "1997-2-1" &
                 ens_results$time_Robj <= "2007-7-1", ]

time_Robj <- seq(as.Date("1997/2/15"), as.Date("2007/7/15"), "month")

livng_cols <- grep('^livng[0-9]*$', names(hhreg))
place_cols <- grep('^place[0-9]*$', names(hhreg))
in_Chitwan <- hhreg[livng_cols]==2 & hhreg[place_cols] <= 151
CVFS_num_psn <- data.frame(time_Robj, num_psn=apply(in_Chitwan, 2, sum, 
                                                na.rm=TRUE))
baseline_num_psn <- ens_results[grep("^(time_Robj|num_psn)", names(ens_results))]
baseline_num_psn$Data_type <- "ABM"
CVFS_num_psn$Data_type <- "CVFS"

baseline_num_psn.means <- with(baseline_num_psn, data.frame(time_Robj, 
                                                          num_psn=num_psn.mean, 
                                                          Data_type))

baseline_num_psn.sds <- baseline_num_psn[grep('time_Robj|sd|Data_type', names(baseline_num_psn))]
names(baseline_num_psn.sds) <- gsub('.sd', '', names(baseline_num_psn.sds))

baseline_num_psn.sds$lim.low <- baseline_num_psn.means$num_psn + 
        2*baseline_num_psn.sds$num_psn
baseline_num_psn.sds$lim.up <- baseline_num_psn.means$num_psn -
        2*baseline_num_psn.sds$num_psn

all_num_psn <- rbind(baseline_num_psn.means, CVFS_num_psn)

p <- ggplot()
p + geom_line(aes(time_Robj, num_psn, linetype=Data_type), 
              data=all_num_psn) +
    geom_ribbon(aes(x=time_Robj, ymin=lim.low, ymax=lim.up),
                alpha=.2, 
                data=baseline_num_psn.sds) +
    scale_fill_discrete(legend=FALSE) + labs(x="Year", y="Sample Population") +
    scale_linetype_discrete(name="Data_type",
                            breaks=c("ABM", "CVFS"),
                            labels=c("ABM", "Observed"))
ggsave("scenario_versus_observed_num_psn.png", width=WIDTH, 
       height=HEIGHT, dpi=DPI)

###############################################################################
# Plot total number of households comparison:
hhid_cols <- grep('^hhid[0-9]*$', names(hhreg))
CVFS_num_HH <- data.frame(time_Robj,
                          num_hs=apply(hhreg[hhid_cols], 2, function(column) 
                                       length(unique(column))))
baseline_num_HH <- ens_results[grep("^(time_Robj|num_hs)", names(ens_results))]
baseline_num_HH$Data_type <- "ABM"
CVFS_num_HH$Data_type <- "CVFS"

baseline_num_HH.means <- with(baseline_num_HH, data.frame(time_Robj, 
                                                          num_hs=num_hs.mean, 
                                                          Data_type))

baseline_num_HH.sds <- baseline_num_HH[grep('time_Robj|sd|Data_type', names(baseline_num_HH))]
names(baseline_num_HH.sds) <- gsub('.sd', '', names(baseline_num_HH.sds))

baseline_num_HH.sds$lim.low <- baseline_num_HH.means$num_hs + 
        2*baseline_num_HH.sds$num_hs
baseline_num_HH.sds$lim.up <- baseline_num_HH.means$num_hs -
        2*baseline_num_HH.sds$num_hs

all_num_HH <- rbind(baseline_num_HH.means, CVFS_num_HH)

p <- ggplot()
p + geom_line(aes(time_Robj, num_hs, linetype=Data_type), 
              data=all_num_HH) +
    geom_ribbon(aes(x=time_Robj, ymin=lim.low, ymax=lim.up),
                alpha=.2, 
                data=baseline_num_HH.sds) +
    scale_fill_discrete(legend=FALSE) + labs(x="Year", y="Number of Households") +
    scale_linetype_discrete(name="Data_type",
                            breaks=c("ABM", "CVFS"),
                            labels=c("ABM", "Observed"))
ggsave("scenario_versus_observed_num_hs.png", width=WIDTH, 
       height=HEIGHT, dpi=DPI)
