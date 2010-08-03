#!/usr/bin/env Rscript
###############################################################################
# Script used to generate a synthetic dataset of individuals, households, and 
# neighborhoods to be used in running the ChitwanABM. This allows both modeling 
# the full population (as the CVFS is only a partial sample), and also allows 
# redistributing the model with an unrestricted population dataset. The CVFS 
# data is restricted access to protect respondent confidentiality.

load("/media/Local_Secure/ChitwanABM_init/hhrel.Rdata")
load("/media/Local_Secure/ChitwanABM_init/hhag.Rdata")
load("/media/Local_Secure/ChitwanABM_init/neigh.Rdata")

# First convert the LULC data to get a total NBH area field, and then make all 
# the other fields percentages of this total.



###############################################################################
# Output data. Synthetic data is NOT restricted so it can be distributed 
# freely.
save(hhrel.syn, file="/media/Local_Secure/ChitwanABM_init/hhrel.Rdata")
save(hhag.syn, file="/media/Local_Secure/ChitwanABM_init/hhag.Rdata")
save(neigh.syn, file="/media/Local_Secure/ChitwanABM_init/neigh.Rdata")
