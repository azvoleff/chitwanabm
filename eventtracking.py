# Copyright 2009 Alex Zvoleff
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

"""
Classes for life events such as marriage, birth, migration, etc. Allows easier 
tracking of these events when plotting results.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import numpy as np

class Results(object):
    def __init__(self):
        self._timesteps = []
        self._months = []
        self._years = []
        self._model_run_ID = None
        self._num_persons = []
        self._num_households = []
        self._num_neighborhoods = []
        self._num_births = []
        self._num_deaths = []
        self._num_marriages = []
        self._num_migrations = []

    def set_model_run_ID(self, model_run_ID):
        "Stores the model run ID for easier tracking of results."
        self._model_run_ID = model_run_ID

    def get_model_run_ID(self):
        "Stores the model run ID for easier tracking of results."
        return self._model_run_ID

    def add_timestep(self, timestep):
        self._timesteps.append(timestep)

    def add_month(self, month):
        self._months.append(month)

    def add_year(self, year):
        self._years.append(year)

    def add_num_persons(self, persons):
        if len(self._num_persons) == (len(self._timesteps) - 1):
            self._num_persons.append(persons)
        else:
            raise Error("number of persons already stored for this timestep")

    def add_num_households(self, households):
        if len(self._num_households) == (len(self._timesteps) - 1):
            self._num_households.append(households)
        else:
            raise Error("number of households already stored for this timestep")

    def add_num_neighborhoods(self, neighborhoods):
        if len(self._num_neighborhoods) == (len(self._timesteps) - 1):
            self._num_neighborhoods.append(neighborhoods)
        else:
            raise Error("number of neighborhoods already stored for this timestep")

    def add_num_births(self, births):
        if len(self._num_births) == (len(self._timesteps) - 1):
            self._num_births.append(births)
        else:
            raise Error("model results already stored for this timestep")

    def add_num_deaths(self, deaths):
        if len(self._num_deaths) == (len(self._timesteps) - 1):
            self._num_deaths.append(deaths)
        else:
            raise Error("number of deaths already stored for this timestep")

    def add_num_marriages(self, marriages):
        if len(self._num_marriages) == (len(self._timesteps) - 1):
            self._num_marriages.append(marriages)
        else:
            raise Error("number of marriages already stored for this timestep")

    def add_num_migrations(self, migrations):
        if len(self._num_migrations) == (len(self._timesteps) - 1):
            self._num_migrations.append(migrations)
        else:
            raise Error("number of migrations already stored for this timestep")

    def get_timesteps(self):
        return self._timesteps

    def get_months(self):
        return self._months

    def get_years(self):
        return self._years

    def get_num_persons(self):
        return self._num_persons

    def get_num_households(self):
        return self._num_households

    def get_num_neighborhoods(self):
        return self._num_neighborhoods

    def get_num_births(self):
        return self._num_births

    def get_num_deaths(self):
        return self._num_deaths

    def get_num_marriages(self):
        return self._num_marriages

    def get_num_migrations(self):
        return self._num_migrations

    def get_results_array(self):
        results_array = np.vstack((self.get_timesteps(), self.get_months(),
            self.get_years(), self.get_num_persons(), self.get_num_households(),
            self.get_num_neighborhoods(), self.get_num_births(),
            self.get_num_deaths(), self.get_num_marriages(),
            self.get_num_migrations()))
        results_array = results_array.transpose()
        row_headings = ['timestep', 'month', 'year', 'pop_psn', 'pop_hs',
                'pop_nbh', 'births', 'deaths', 'marr', 'mig']
        results_array = np.vstack((row_headings, results_array))
        return results_array
