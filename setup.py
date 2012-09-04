import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name = "chitwanabm",
    version = "1.5dev",
    packages = find_packages(),
    include_package_data = True,
    exclude_package_data = {'': ['.gitignore']},
    zip_safe = True,
    install_requires = ['docutils >= 0.3',
                        'setuptools_git >= 0.3',
                        'numpy >= 1.6.2',
                        'pyabm >= 0.3'],
    author = "Alex Zvoleff",
    author_email = "azvoleff@mail.sdsu.edu",
    description = "An agent-based model of the Chitwan Valley, Nepal",
    license = "GPL v3 or later",
    keywords = "agent-based modeling ABM simulation model",
    url = "http://rohan.sdsu.edu/~zvoleff/ChitwanABM.php",   # project home page, if any
    long_description = """
chitwanabm is an agent-based model of the Western Chitwan Valley, Nepal.  
The model represents a subset of the population of the Valley using a 
number of agent types (person, household and neighborhood agents), 
environmental variables (topography, land use and land cover) and social 
context variables.

Construction of the model is supported as part of an ongoing National 
Science Foundation Partnerships for International Research and Education 
(NSF PIRE) project `(grant OISE 0729709) <http://pire.psc.isr.umich.edu>`_ 
investigating human-environment interactions in the Western Chitwan Valley. 
Development of the model is in progress, and model documentation is still 
incomplete.  As work continues, this page will be updated with more 
information on initializing and running the model, and on interpreting the 
model output.

See the `chitwanabm website 
<http://rohan.sdsu.edu/~zvoleff/research/ChitwanABM.php>`_ for more 
information, past releases, publications, and recent presentations.
""",
    classifiers = [
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Life",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7"]
)
