require(reshape) # For 'melt' command
require(ggplot2, quietly=TRUE)
WIDTH = 8.33
HEIGHT = 5.53
DPI = 300
theme_update(theme_grey(base_size=18))
update_geom_defaults("line", aes(size=1))

nofb <- read.csv("R:/Data/Nepal/ChitwanABM_runs/USIALE2012_nofeedback/fw_usage_ens_results.csv")
names(nofb) <- gsub('fw_usage_metrictons', 'nofb', names(nofb))
midfb <- read.csv("R:/Data/Nepal/ChitwanABM_runs/USIALE2012_midfeedback/fw_usage_ens_results.csv")
names(midfb) <- gsub('fw_usage_metrictons', 'midfb', names(midfb))
lowfb <- read.csv("R:/Data/Nepal/ChitwanABM_runs/USIALE2012_lowfeedback/fw_usage_ens_results.csv")
names(lowfb) <- gsub('fw_usage_metrictons', 'lowfb', names(lowfb))
highfb <- read.csv("R:/Data/Nepal/ChitwanABM_runs/USIALE2012_highfeedback/fw_usage_ens_results.csv")
names(highfb) <- gsub('fw_usage_metrictons', 'highfb', names(highfb))

fw_scenarios <- merge(nofb, lowfb)
fw_scenarios <- merge(fw_scenarios, midfb)
fw_scenarios <- merge(fw_scenarios, highfb)

meancols <- grep('mean', names(fw_scenarios))
fw_means <- data.frame(time_Robj=fw_scenarios$time.Robj, fw_scenarios[meancols])
fw_means <- melt(fw_means, id='time_Robj')
fw_means$variable <- gsub('.mean', '', fw_means$variable)
names(fw_means)[names(fw_means) == "value"] <- "fwmean"
names(fw_means)[names(fw_means) == "variable"] <- "scenario"

sdcols <- grep('sd', names(fw_scenarios))
fw_sds <- data.frame(time_Robj=fw_scenarios$time.Robj, fw_scenarios[sdcols])
fw_sds <- melt(fw_sds, id='time_Robj')
fw_sds$variable <- gsub('.sd', '', fw_sds$variable)
names(fw_sds)[names(fw_sds) == "value"] <- "sd"
names(fw_sds)[names(fw_sds) == "variable"] <- "scenario"

fw_results <- merge(fw_means, fw_sds)
fw_results$bound.low <- fw_results$fwmean - 2*fw_results$sd
fw_results$bound.high <- fw_results$fwmean + 2*fw_results$sd
fw_results$scenario <- factor(fw_results$scenario)
fw_results$time_Robj <- as.Date(fw_results$time_Robj)
fw_results$scenario <- ordered(fw_results$scenario, levels=c("nofb", "lowfb", "midfb", "highfb"))

fw_results <- fw_results[!(fw_results$scenario=="midfb"),]
fw_results <- fw_results[fw_results$time_Robj>"1998-01-01",]

# Plot fw consumption in metric tons
p <- ggplot()
p + geom_line(aes(time_Robj, fwmean, colour=scenario), data=fw_results) +
    geom_ribbon(aes(x=time_Robj, ymin=bound.low, ymax=bound.high, fill=scenario, alpha=.2), data=fw_results) +
    scale_fill_discrete(name="Model Type",
                            breaks=c("nofb", "lowfb", "midfb", "highfb"),
                            labels=c("No Feedback", "Low Feedback",
                                     "Mid Feedback", "High Feedback")) +
    scale_colour_discrete(name="Model Type",
                            breaks=c("nofb", "lowfb", "midfb", "highfb"),
                            labels=c("No Feedback", "Low Feedback",
                                     "Mid Feedback", "High Feedback")) +
    labs(x="Time", y="Metric Tons of Fuelwood / Month")
ggsave("fuelwood_usage.png", width=WIDTH, height=HEIGHT, dpi=DPI)
