calc_NBH_LULC <- function(DATA_PATH) {
    # Make plots of LULC for a model run.
    lulc <- read.csv(paste(DATA_PATH, "LULC_results.csv", sep="/"))
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

calc_NBH_pop<- function(DATA_PATH) {
    model.results <- read.csv(paste(DATA_PATH, "pop_results.csv", sep="/"))
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
