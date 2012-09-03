#!/usr/bin/env Rscript

require(reshape) # For 'melt' command
require(ggplot2, quietly=TRUE)

WIDTH = 8.33
HEIGHT = 5.53
DPI = 300
theme_update(theme_grey(base_size=18))
update_geom_defaults("line", aes(size=1))

# low_scenario_path  <- "/media/Zvoleff_Passport/Data/Nepal/chitwanabm_runs/225_fission"
# mid_scenario_path <- "/media/Zvoleff_Passport/Data/Nepal/chitwanabm_runs/Baseline"
# high_scenario_path <- "/media/Zvoleff_Passport/Data/Nepal/chitwanabm_runs/375_fission"
# low_scenario_name <- ".225 HH Fission Rate"
# mid_scenario_name <- ".300 HH Fission Rate"
# high_scenario_name <- ".375 HH Fission Rate"

# low_scenario_path  <- "/media/Zvoleff_Passport/Data/Nepal/chitwanabm_runs/150_fission"
# mid_scenario_path <- "/media/Zvoleff_Passport/Data/Nepal/chitwanabm_runs/Baseline"
# high_scenario_path <- "/media/Zvoleff_Passport/Data/Nepal/chitwanabm_runs/600_fission"
# low_scenario_name <- ".150 HH Fission Rate"
# mid_scenario_name <- ".300 HH Fission Rate"
# high_scenario_name <- ".600 HH Fission Rate"

# low_scenario_path <- "/media/Zvoleff_Passport/Data/Nepal/chitwanabm_runs/0395_perm_outmig"
# mid_scenario_path <- "/media/Zvoleff_Passport/Data/Nepal/chitwanabm_runs/Baseline"
# high_scenario_path <- "/media/Zvoleff_Passport/Data/Nepal/chitwanabm_runs/1185_perm_outmig"
# low_scenario_name <- ".0395 Perm. Outmig. Rate"
# mid_scenario_name <- ".0795 Perm. Outmig. Rate"
# high_scenario_name <- ".1185 Perm. Outmig. Rate"

low_scenario_path <- "/media/Zvoleff_Passport/Data/Nepal/chitwanabm_runs/low_des_num_child"
mid_scenario_path <- "/media/Zvoleff_Passport/Data/Nepal/chitwanabm_runs/Baseline"
high_scenario_path <- "/media/Zvoleff_Passport/Data/Nepal/chitwanabm_runs/high_des_num_child"
low_scenario_name <- "Fewer Children"
mid_scenario_name <- "Baseline"
high_scenario_name <- "More Children"
 
plot_scenario_comparison <- function(result_file_name, low_name, mid_name, 
                                     high_name, var_name, ylabel) {
    low_scenario <- read.csv(paste(low_scenario_path, result_file_name, 
                                   sep="/"))
    names(low_scenario) <- gsub(var_name, 'low', names(low_scenario))
    mid_scenario <- read.csv(paste(mid_scenario_path, result_file_name, 
                                   sep="/"))
    names(mid_scenario) <- gsub(var_name, 'mid', names(mid_scenario))
    high_scenario <- read.csv(paste(high_scenario_path, result_file_name, 
                                    sep="/"))
    names(high_scenario) <- gsub(var_name, 'high', names(high_scenario))
    needed_cols <- grep('^(time.Robj|low)', names(low_scenario))
    scenarios <- merge(low_scenario[needed_cols], mid_scenario[needed_cols])
    scenarios <- merge(scenarios, high_scenario[needed_cols])

    meancols <- grep('mean', names(scenarios))
    means <- data.frame(time_Robj=scenarios$time.Robj, scenarios[meancols])
    means <- melt(means, id='time_Robj')
    means$variable <- gsub('.mean', '', means$variable)
    names(means)[names(means) == "value"] <- "varmean"
    names(means)[names(means) == "variable"] <- "scenario"

    sdcols <- grep('sd', names(scenarios))
    sds <- data.frame(time_Robj=scenarios$time.Robj, scenarios[sdcols])
    sds <- melt(sds, id='time_Robj')
    sds$variable <- gsub('.sd', '', sds$variable)
    names(sds)[names(sds) == "value"] <- "sd"
    names(sds)[names(sds) == "variable"] <- "scenario"

    results <- merge(means, sds)
    results$bound.low <- results$varmean - 2*results$sd
    results$bound.high <- results$varmean + 2*results$sd
    results$scenario <- factor(results$scenario)
    results$time_Robj <- as.Date(results$time_Robj)
    results$scenario <- ordered(results$scenario, levels=c("low", "mid", 
                                                                 "high"))
    results <- results[results$time_Robj>"1997-01-01",]

    p <- ggplot()
    p + geom_line(aes(time_Robj, varmean, colour=scenario), data=results) +
        geom_ribbon(aes(x=time_Robj, ymin=bound.low, ymax=bound.high, 
                        fill=scenario, alpha=.2), data=results) +
        scale_fill_discrete(name="Scenario",
                                breaks=c("low", "mid", "high"),
                                labels=c(low_scenario_name, mid_scenario_name, 
                                    high_scenario_name)) +
        scale_colour_discrete(name="Scenario",
                                breaks=c("low", "mid", "high"),
                                labels=c(low_scenario_name, mid_scenario_name, 
                                         high_scenario_name)) +
        scale_alpha(guide=FALSE) +
        labs(x="Time", y=ylabel)
    ggsave(paste("scenario_comparison_", var_name, ".png", sep=""), 
           width=WIDTH, height=HEIGHT, dpi=DPI)
}


plot_scenario_comparison("fw_usage_ens_results.csv", 
                         low_scenario_name,mid_scenario_name, 
                         high_scenario_name, 'fw_usage_metrictons',
                         "Metric Tons of Fuelwood / Month")

plot_scenario_comparison("ens_results_pop.csv", 
                         low_scenario_name, mid_scenario_name, 
                         high_scenario_name, 'num_psn',
                         "Total Population")

plot_scenario_comparison("ens_results_pop.csv", 
                         low_scenario_name, mid_scenario_name, 
                         high_scenario_name, 'num_hs',
                         "Number of Households")

plot_scenario_comparison("ens_results_LULC.csv", 
                         low_scenario_name, mid_scenario_name, 
                         high_scenario_name, 'agveg',
                         "Percent Agricultural Vegetation")

plot_scenario_comparison("ens_results_LULC.csv", 
                         low_scenario_name, mid_scenario_name, 
                         high_scenario_name, 'privbldg',
                         "Percent Private Buildings")
