Overview of CHEEREIO's capabilities
==========

What CHEEREIO can do with 4D-LETKF
-------------

CHEEREIO is a tool for chemical data assimilation characterized by its flexibility. It can assimilate any kind of observation (satellite, surface, or aircraft) for any species in any configuration of GEOS-Chem, applying updates to both emissions scaling factors and chemical concentrations. CHEEREIO allows for wide flexibility in what can be assimilated, and for example allows for the user to (1) update observations at multiple time points in the assimilation window (e.g. hourly data updates for a daily window), and (2) assimilate observations of derived quantities such as PM\ :sub:`2.5` or AOD. This is because CHEEREIO needs to load history files to gather concentrations, rather than just restart files which are sufficient for instantaneous ("3D") assimilation.

Many different kinds of observations can be used at once to update a family of species. For example, one might want to use NO\ :sub:`2` satellite and surface data, SO\ :sub:`2` satellite and surface data, NH\ :sub:`3` satellite data, AOD, and surface PM\ :sub:`2.5` to update emissions and concentrations of NO, NO\ :sub:`2`\ , SO\ :sub:`2`\ , and NH\ :sub:`3` along with concentrations of SO\ :sub:`4`, NO\ :sub:`y`, and NH\ :sub:`4`. Whether applying this sort of update in a small nested region or for a global simulation, CHEEREIO can be configured to support just about any kind of chemical data assimilation problem.

What CHEEREIO can't do
-------------

The 4D-LETKF algorithm that undergirds CHEEREIO is complex (see :ref:`Further Reading` on the About page for more details), and its application to chemical data assimilation remains an area of active research. You should approach this tool with caution and evaluate your results carefully. CHEEREIO is a purely statistical tool and will not warn you if it is merely assimilating noise. For example, you could configure CHEEREIO to use observations of SO\ :sub:`2` to update emissions of isoprene thousands of kilometers away. Such an observation will provide little information, and any updates will likely be a result of statistical noise that may still look like a signal in some cases. In short, spend lots of time thinking about which control and state vector settings will be most informative for your particular problem. CHEEREIO cannot tell you if your settings are reasonable, nor can it provide sensible updates emissions or concentrations of species unilluminated by observations.

Postprocessing tools
-------------

CHEEREIO comes with a suite of postprocessing tools and pre-built workflows in the ``postprocess/`` folder of the main CHEEREIO code directory. In particular, the SLURM batch script ``postprocess_prep.batch`` will automatically create a variety of figures, movies, and consolidated data files that the user can then view and modify. To supplement these auto-generated files and figures, more useful functions are included in the ``postprocess_tools.py`` file. More information is provided in the :ref:`Postprocessing workflow` page.