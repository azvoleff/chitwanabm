chitwanabm Model Code
======================

Overview
_________

The chitwanabm represents the population of the Chitwan Valley Family Study 
sample using a hierarchical structure of agents. Person agents are nested 
within household agents, which are nested within neighborhood agents.

The chitwanabm model code uses two primary classes (which are found in the 
PyABM package) to represent these agents: the ``Agent`` class, and the 
``Agent-set`` class.  The ``Agent-set`` class is a subclass of the ``Agent`` 
class, which is used to represent agents that are 'sets' of other, lower-level 
agents. For example, the ``Household`` class in the chitwanabm is a subclass of 
the ``Agent-set`` class, which contains a set of ``Person`` class instances.  
The ``Person`` class is a subclass of the ``Agent`` class - not of the 
``Agent-set`` class, because person agents are the lowest level agent 
represented in the chitwanabm.

Code Reference
_____________________

:mod:`agents` Module
--------------------

.. automodule:: chitwanabm.agents
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`initialize` Module
------------------------

.. automodule:: chitwanabm.initialize
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`modelloop` Module
-----------------------

.. automodule:: chitwanabm.modelloop
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`runmodel` Module
----------------------

.. automodule:: chitwanabm.runmodel
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`statistics` Module
------------------------

.. automodule:: chitwanabm.statistics
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`test` Module
------------------

.. automodule:: chitwanabm.test
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`threaded_batch_run` Module
--------------------------------

.. automodule:: chitwanabm.threaded_batch_run
    :members:
    :undoc-members:
    :show-inheritance:

