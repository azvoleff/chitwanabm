# Contains functions used to calculate and plot neighborhood-level statistics 
# from a single model run, or from an ensemble of model runs.

require(ggplot2, quietly=TRUE)

calc_NBH_LULC <- function(DATA_PATH, timestep) {
    # Make plots of LULC for a model run.
    # 276.csv
    lulc <- read.csv(paste(DATA_PATH, "/NBHs_time_", timestep, ".csv", sep=""))

    agveg.col <- grep('^agveg.*$', names(lulc))
    nonagveg.col <- grep('^nonagveg.*$', names(lulc))
    pubbldg.col <- grep('^pubbldg.*$', names(lulc))
    privbldg.col <- grep('^privbldg.*$', names(lulc))
    other.col <- grep('^other.*$', names(lulc))

    # Calculate the total land area of each neighborhood
    nbh.area <- apply(cbind(lulc$agveg, lulc$nonagveg, lulc$pubbldg,
            lulc$privbldg, lulc$other), 1, sum)

    # And convert the LULC measurements from units of square meters to units 
    # that are a percentage of total neighborhood area.
    lulc.sd <- lulc/nbh.area

    lulc.nbh <- data.frame(nid=lulc$nid, x=lulc$x, y=lulc$y, agveg=lulc.sd[agveg.col],
            nonagveg=lulc.sd[nonagveg.col], pubbldg=lulc.sd[pubbldg.col],
            privbldg=lulc.sd[privbldg.col], other=lulc.sd[other.col])

    return(lulc.nbh)
}


calc_agg_LULC <- function(DATA_PATH) {
    # Make plots of LULC for a model run.
    lulc <- read.csv(paste(DATA_PATH, "run_results.csv", sep="/"),
            na.strings=c("NA", "nan"))
    time.values <- read.csv(paste(DATA_PATH, "time.csv", sep="/"))
    time.Robj <- as.Date(paste(time.values$time_date, "15", sep=","),
            format="%m/%Y,%d")
    time.values <- cbind(time.values, time.Robj=time.Robj)

    agveg.cols <- grep('^agveg.[0-9]*$', names(lulc))
    nonagveg.cols <- grep('^nonagveg.[0-9]*$', names(lulc))
    pubbldg.cols <- grep('^pubbldg.[0-9]*$', names(lulc))
    privbldg.cols <- grep('^privbldg.[0-9]*$', names(lulc))
    other.cols <- grep('^other.[0-9]*$', names(lulc))

    # Calculate the total land area of each neighborhood
    nbh.area <- apply(cbind(lulc$agveg.1, lulc$nonagveg.1, lulc$pubbldg.1,
            lulc$privbldg.1, lulc$other.1), 1, sum)

    # And convert the LULC measurements from units of square meters to units 
    # that are a percentage of total neighborhood area.
    lulc.sd <- lulc/nbh.area
    lulc.sd.mean <- data.frame(time.Robj=time.Robj,
            agveg=apply(lulc.sd[agveg.cols], 2, mean),
            nonagveg=apply(lulc.sd[nonagveg.cols], 2, mean),
            pubbldg=apply(lulc.sd[pubbldg.cols], 2, mean),
            privbldg=apply(lulc.sd[privbldg.cols], 2, mean),
            other=apply(lulc.sd[other.cols], 2, mean), row.names=NULL)

    return(lulc.sd.mean)
}

calc_NBH_pop <- function(DATA_PATH) {
    model.results <- read.csv(paste(DATA_PATH, "run_results.csv", sep="/"),
            na.strings=c("NA", "nan"))
    # Read in time data to use in plotting. time.Robj will provide the x-axis 
    # values.
    time.values <- read.csv(paste(DATA_PATH, "time.csv", sep="/"))
    time.Robj <- as.Date(paste(time.values$time_date, "15", sep=","),
            format="%m/%Y,%d")
    time.values <- cbind(time.values, time.Robj=time.Robj)

    num_psn.cols <- grep('^num_psn.[0-9]*$', names(model.results))
    num_hs.cols <- grep('^num_hs.[0-9]*$', names(model.results))
    # num_marr is total number of marriages in the neighborhood, whereas marr is 
    # the number of new marriages in a particular month.
    num_marr.cols <- grep('^num_marr.[0-9]*$', names(model.results))
    marr.cols <- grep('^marr.[0-9]*$', names(model.results))
    births.cols <- grep('^births.[0-9]*$', names(model.results))
    deaths.cols <- grep('^deaths.[0-9]*$', names(model.results))
    in_migr.cols <- grep('^in_migr.[0-9]*$', names(model.results))
    out_migr.cols <- grep('^out_migr.[0-9]*$', names(model.results))
    fw_usage.cols <- grep('^fw_usage.[0-9]*$', names(model.results))

    model.results <- data.frame(time.Robj=time.Robj,
            marr=apply(model.results[marr.cols], 2, sum, na.rm=TRUE), 
            births=apply(model.results[births.cols], 2, sum, na.rm=TRUE), 
            deaths=apply(model.results[deaths.cols], 2, sum, na.rm=TRUE),
            in_migr=apply(model.results[in_migr.cols], 2, sum, na.rm=TRUE), 
            out_migr=apply(model.results[out_migr.cols], 2, sum, na.rm=TRUE),
            num_hs=apply(model.results[num_hs.cols], 2, sum, na.rm=TRUE), 
            num_marr=apply(model.results[num_marr.cols], 2, sum, na.rm=TRUE),
            num_psn=apply(model.results[num_psn.cols], 2, sum, na.rm=TRUE),
            fw_usage_kg=apply(model.results[fw_usage.cols], 2, sum, na.rm=TRUE))
    return(model.results)
}

make_shaded_error_plot <- function(ens_res, ylabel, typelabel) {
    # The first column of ens_res dataframe should be the times
    # For each variable listed in "variable_names", there should be two columns,
    # one of means, named "variable_name.mean" and one of standard deviations,
    # named "variable_name.sd"
    theme_update(theme_grey(base_size=18))
    update_geom_defaults("line", aes(size=1))

    # Ignore column one in code in next line since it is only the time
    var_names <- unique(gsub("(.mean)|(.sd)", "",
                    names(ens_res)[2:ncol(ens_res)]))
    num_vars <- length(var_names)
    time.Robj <- ens_res$time.Robj

    # Stack the data to use in ggplot2
    mean.cols <- grep(".mean$", names(ens_res))
    sd.cols <- grep(".sd$", names(ens_res))
    ens_res.mean <- stack(data.frame(ens_res$time.Robj, ens_res[mean.cols]))
    # Need the *2 below because each var has two cols, one for sd and one for 
    # mean
    ens_res.mean <- cbind(time.Robj=rep(time.Robj,num_vars*2), ens_res.mean)
    names(ens_res.mean)[2:3] <- c("mean", "Type")
    # Remove the ".mean" appended to the Type values (agveg.mean, 
    # nonagveg.mean, etc) so that it does not appear in the plot legend.
    ens_res.mean$Type <- gsub(".mean", "", ens_res.mean$Type)
    ens_res.sd <- stack(data.frame(ens_res$time.Robj, ens_res[sd.cols]))
    ens_res.sd <- cbind(time.Robj=rep(time.Robj,num_vars*2), ens_res.sd)
    names(ens_res.sd)[2:3] <- c("sd", "Type")

    # Add lower and upper limits of ribbon to ens_res.sd dataframe
    ens_res.sd <- cbind(ens_res.sd, lim.up=ens_res.mean$mean + 2*ens_res.sd$sd)
    ens_res.sd <- cbind(ens_res.sd, lim.low=ens_res.mean$mean - 2*ens_res.sd$sd)

    p <- ggplot()
    if (is.na(typelabel)) {
        # Don't use types - used for plotting things like fuelwood and total 
        # populatation, where there is only one class on the plot.
        p + geom_line(aes(time.Robj, mean), data=ens_res.mean) +
            geom_ribbon(aes(x=time.Robj, ymin=lim.low, ymax=lim.up),
                alpha=.2, data=ens_res.sd) +
            scale_fill_discrete(legend=F) +
            labs(x="Years", y=ylabel)
    }
    else {
        p + geom_line(aes(time.Robj, mean, colour=Type), data=ens_res.mean) +
            geom_ribbon(aes(x=time.Robj, ymin=lim.low, ymax=lim.up, fill=Type),
                alpha=.2, data=ens_res.sd) +
            scale_fill_discrete(legend=F) +
            labs(x="Years", y=ylabel, colour=typelabel)
    }
}

calc_ensemble_results <- function(model_results) {
    # The first column of model_results dataframe should be the times
    # For each variable listed in "variable_names", there should be two columns,
    # one of means, named "variable_name.mean" and one of standard deviations,
    # named "variable_name.sd"
    var_names <- unique(gsub(".run[0-9]*$", "",
                    names(model_results)[2:ncol(model_results)]))
    var_names <- var_names[var_names!="time.Robj"]

    # First calculate the mean and standard deviations for each set of runs
    ens_res <- data.frame(time.Robj=model_results$time.Robj.run1)
    for (var_name in var_names) {
        var_cols <- grep(paste("^", var_name, ".", sep=""), names(model_results))
        var_mean <- apply(model_results[var_cols], 1, mean)
        var_sd <- apply(model_results[var_cols], 1, sd)
        ens_res <- cbind(ens_res, var_mean, var_sd)
        var_mean.name <- paste(var_name, ".mean", sep="")
        var_sd.name <- paste(var_name, ".sd", sep="")
        names(ens_res)[(length(ens_res)-1):length(ens_res)] <- c(var_mean.name, var_sd.name)
    }
    return(ens_res)
}

calc_ensemble_results_NBH <- function(model_results) {
    # This function returns neighborhood level mean and standard deviations 
    # from an ensemble at a single timestep.
    # The first column of model_results dataframe should be the times
    # For each variable listed in "variable_names", there should be two columns,
    # one of means, named "variable_name.mean" and one of standard deviations,
    # named "variable_name.sd"
    var_names <- unique(gsub(".run[0-9]*$", "",
                    names(model_results)[2:ncol(model_results)]))
    var_names <- var_names[!(var_names %in% c("nid", "x", "y"))]

    # First calculate the mean and standard deviations for each set of runs
    ens_res <- data.frame(nid=model_results$nid, x=model_results$x, y=model_results$y)
    for (var_name in var_names) {
        var_cols <- grep(paste("^", var_name, ".", sep=""), names(model_results))
        var_mean <- apply(model_results[var_cols], 1, mean)
        var_sd <- apply(model_results[var_cols], 1, sd)
        ens_res <- cbind(ens_res, var_mean, var_sd)
        var_mean.name <- paste(var_name, ".mean", sep="")
        var_sd.name <- paste(var_name, ".sd", sep="")
        names(ens_res)[(length(ens_res)-1):length(ens_res)] <- c(var_mean.name, var_sd.name)
    }
    return(ens_res)
}
