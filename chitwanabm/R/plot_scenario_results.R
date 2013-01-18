#!/usr/bin/env Rscript

require(reshape) # For 'melt' command
require(ggplot2, quietly=TRUE)

WIDTH = 8.33
HEIGHT = 5.53
DPI = 300
theme_set(theme_grey(base_size=18))
update_geom_defaults("line", aes(size=.5))
default_scale_colour <- function(...) {scale_colour_brewer(palette="Dark2", ...)}
default_scale_fill <- function(...) {scale_fill_brewer(palette="Dark2", ...)}
scale_colour_discrete <- default_scale_colour
scale_fill_discrete <- default_scale_fill

items <- list(list("HH_Fission",
                   list(c("No_Feedbacks_no_LULC_model", "No effect"),
                        c("HH_Fission_Low_nofeedbacks", "Half calculated rate"),
                        c("HH_Fission_High_nofeedbacks", "Double calculated rate"))),
              list("combined",
                   list(c("Baseline", "Baseline"),
                        c("No_Feedbacks_no_LULC_model", "No effect"),
                        c("Combined_Half_Feedbacks", "Half calculated effect"),
                        c("Combined_Double_Feedbacks", "Double calculated effect"))),
              list("marriagetiming",
                   list(c("Baseline_marriagescenarios", "Baseline"),
                        c("No_Feedbacks_no_LULC_model", "No effect"),
                        c("Half_Feedbacks_marriagescenarios", "Half calculated effect"),
                        c("Double_Feedbacks_marriagescenarios", "Double calculated effect"))),
              list("firstbirth",
                   list(c("Baseline_firstbirthscenarios", "Baseline"),
                        c("No_Feedbacks_no_LULC_model", "No effect"),
                        c("Half_Feedbacks_firstbirthscenarios", "Half calculated effect"),
                        c("Double_Feedbacks_firstbirthscenarios", "Double calculated effect"))))

plot_scenario_comparison <- function(result_file_name, var_name, ylabel, 
                                     scenario_info, ylims=NA, aggtype=NA, 
                                     aggtype_field=NA, suffix="") {
    scenario_name <- scenario_info[[1]]
    scenarios <- scenario_info[[2]]

    legend_breaks <- c()
    legend_labels <- c()
    for (n in 1:length(scenarios)) {
        scenario <- scenarios[[n]]
        legend_break <- paste('scenario', n, sep="_")
        scenario_data <- read.csv(paste(scenario[[1]], result_file_name, 
                                        sep="/"))
        names(scenario_data) <- gsub(var_name, legend_break, names(scenario_data))
        legend_breaks <- c(legend_breaks, legend_break)
        legend_labels <- c(legend_labels, scenario[[2]])
        needed_cols <- grep(paste('^(time.Robj|', legend_break, ')', sep=''), names(scenario_data))
        if (!is.na(aggtype_field)) {
            needed_cols <- c(needed_cols, grep(aggtype_field, 
                                               names(scenario_data)))
        }
        scenario_data <- scenario_data[needed_cols]
        if (n == 1) {
            all_scenario_data <- scenario_data
        } else {
            all_scenario_data <- merge(all_scenario_data, scenario_data)
        }
    }

    if ((!is.na(aggtype) & is.na(aggtype_field)) |
        (is.na(aggtype) & !is.na(aggtype_field))) {
        stop("Must specify both aggtype and aggtype_field")
    } else if (sum(grepl(paste("^", aggtype_field, "$", sep=""), names(all_scenario_data)) >= 1) & !is.na(aggtype)) {
        aggtype_col <- grep(paste("^", aggtype_field, "$", sep=""), names(all_scenario_data))
        if (length(aggtype_col) < 1) {
            stop(paste("aggregation field", aggtype_field, "not found"))
        }
        all_scenario_data <- all_scenario_data[all_scenario_data[aggtype_col] == aggtype,]
    }

    meancols <- grep('mean$', names(all_scenario_data))
    means <- data.frame(time_Robj=all_scenario_data$time.Robj, all_scenario_data[meancols])
    means <- melt(means, id='time_Robj')
    means$variable <- gsub('.mean', '', means$variable)
    names(means)[names(means) == "value"] <- "varmean"
    names(means)[names(means) == "variable"] <- "scenario"

    sdcols <- grep('sd$', names(all_scenario_data))
    sds <- data.frame(time_Robj=all_scenario_data$time.Robj, all_scenario_data[sdcols])
    sds <- melt(sds, id='time_Robj')
    sds$variable <- gsub('.sd', '', sds$variable)
    names(sds)[names(sds) == "value"] <- "sd"
    names(sds)[names(sds) == "variable"] <- "scenario"

    results <- merge(means, sds)
    results$bound.low <- results$varmean - 2*results$sd
    results$bound.high <- results$varmean + 2*results$sd
    results$scenario <- factor(results$scenario)
    results$time_Robj <- as.Date(results$time_Robj)
    results$scenario <- ordered(results$scenario, levels=legend_breaks)
    results <- results[results$time_Robj>"1997-01-01",]

    p <- ggplot()
    p <- p + geom_line(aes(time_Robj, varmean, colour=scenario, linetype=scenario), data=results) +
        geom_ribbon(aes(x=time_Robj, ymin=bound.low, ymax=bound.high, 
                        fill=scenario, alpha=.2), data=results) +
        scale_fill_discrete(guide=FALSE) +
        scale_colour_discrete(name="Scenario",
                                breaks=legend_breaks,
                                labels=legend_labels) +
        scale_linetype_discrete(name="Scenario",
                                breaks=legend_breaks,
                                labels=legend_labels) +
        scale_alpha(guide=FALSE) +
        labs(x="Time", y=ylabel)
    if (!is.na(ylims[1]) && !is.na(ylims[2])) {
        p <- p + ylim(ylims[1], ylims[2])
    }
    p
    ggsave(paste(scenario_name, "_", var_name, suffix, ".png", sep=""), 
           width=WIDTH, height=HEIGHT, dpi=DPI)
}

for (item_num in 1:length(items)) {
    scenario_info <- items[[item_num]]

    plot_scenario_comparison("fw_usage_ens_results.csv", 'fw_usage_metrictons',
                             "Metric Tons of Fuelwood / Month", scenario_info,
                             ylims=c(0, 85))

    plot_scenario_comparison("ens_results_pop.csv", 'num_psn',
                             "Total Population", scenario_info,
                             ylims=c(7500, 25500))

    plot_scenario_comparison("ens_results_pop.csv", 'num_hs',
                             "Number of Households", scenario_info,
                             ylims=c(1500, 9000))

    plot_scenario_comparison("ens_results_LULC.csv", 'agveg',
                             "Percent Agricultural Vegetation", scenario_info,
                             ylims=c(.15, .7))

    plot_scenario_comparison("ens_results_LULC.csv", 'privbldg',
                             "Percent Private Buildings", scenario_info,
                             ylims=c(.15, .7))

    plot_scenario_comparison("ens_results_marriage_rates.csv", 'marriages',
                             "Marriage Rate (per 1000 residents)", 
                             scenario_info, aggtype="Urban", 
                             aggtype_field="lctype", suffix='_urban_nbhs')

    plot_scenario_comparison("ens_results_marriage_rates.csv", 'marriages',
                             "Marriage Rate (per 1000 residents)", 
                             scenario_info, aggtype="Agricultural",
                             aggtype_field="lctype", suffix='_ag_nbhs')

    plot_scenario_comparison("ens_results_marriage_ages_female.csv", 'marr_age',
                             "Marriage age", scenario_info, ylims=c(17, 24), 
                             aggtype="1st quartile", aggtype_field="lcctype", 
                             suffix='_urban_nbhs')

    plot_scenario_comparison("ens_results_marriage_ages_female.csv", 'marr_age',
                             "Marriage age", scenario_info, ylims=c(17, 24), 
                             aggtype="4th quartile", aggtype_field="lcctype",
                             suffix='_ag_nbhs')

    plot_scenario_comparison("ens_results_fb_ints.csv", 'fb_int',
                             "First birth time (months)", scenario_info, 
                             aggtype="1st quartile", aggtype_field="lcctype", 
                             suffix='_urban_nbhs', ylims=c(8, 35))

    plot_scenario_comparison("ens_results_fb_ints.csv", 'fb_int',
                             "First birth time (months)", scenario_info, 
                             aggtype="4th quartile", aggtype_field="lcctype",
                             suffix='_ag_nbhs', ylims=c(8, 35))
}
