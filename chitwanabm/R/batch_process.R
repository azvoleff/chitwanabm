#!/usr/bin/env Rscript
#
# Copyright 2008-2013 Alex Zvoleff
#
# This file is part of the chitwanabm agent-based model.
# 
# chitwanabm is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# chitwanabm is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# chitwanabm.  If not, see <http://www.gnu.org/licenses/>.
#
# See the README.rst file for author contact information.

DATA_PATH <- shQuote(commandArgs(trailingOnly=TRUE)[1])
if (is.na(DATA_PATH)) stop("Data path must be supplied")

initial.options <- commandArgs(trailingOnly = FALSE)
file.arg.name <- "--file="
script.name <- sub(file.arg.name, "", initial.options[grep(file.arg.name, initial.options)])
script.basename <- dirname(script.name)

R_bin <- '"C:/Program Files/R/R-2.15.2/bin/x64/Rscript.exe"'
shell(paste(R_bin, paste(script.basename, 'batch_calculations.R', sep="/"), DATA_PATH))
shell(paste(R_bin, paste(script.basename, 'batch_plots.R', sep="/"), DATA_PATH))
