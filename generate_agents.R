#!/usr/bin/env Rscript
#
# Copyright 2008-2012 Alex Zvoleff
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

###############################################################################
# Script used to generate a synthetic dataset of individuals, households, and 
# neighborhoods to be used in running the ChitwanABM. This allows both modeling 
# the full population (as the CVFS is only a partial sample), and also allows 
# redistributing the model with an unrestricted population dataset. The CVFS 
# data is restricted access to protect respondent confidentiality.
###############################################################################

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
