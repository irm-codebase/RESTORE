# The RESTORE model
RESTORE: RetrospEctive SecTor cOupled eneRgy toolsEt

## Short description
RESTORE is based on D-EXPANSE, a stylized national-level power system model used in hindcasting studies:
- Trutnevyte: [Does cost optimization approximate the real-world energy transition?](http://dx.doi.org/10.1016/j.energy.2016.03.038)
- Wen et al.: [Accuracy indicators for evaluating retrospective performance of energy system models](https://doi.org/10.1016/j.apenergy.2022.119906)
- Wen et al.: [Hindcasting to inform the development of bottom-up electricity system models: The cases of endogenous demand and technology learning](https://doi.org/10.1016/j.apenergy.2023.121035)

RESTORE builds on D-EXPANSE by implementing graph-based energy flows, spatial-disaggregation and sector-coupling capabilities (similar to TIMES, TEMOA, OSeMOSYS, etc.). The entire model architecture has been reworked to improve readability, featuring generic constraints that can be easily re-used in sector modules defined by developers.

RESTORE also features a fully standardized prototyping workflow based on [FAIR principles](https://www.go-fair.org/fair-principles/). Model components (called "entities") are defined in single files, where the user can specify parameter names, values, units and sources. These files are rapidly converted into a single configuration file that the model uses as input. Conversion of currencies, energy units and power units is also integrated into this process.

This lets model developers track the sources of their data, and gives users and other researchers full transparency into the model's operation and assumptions.

## IMPORTANT

RESTORE is ***not a model validation tool***. Although hindcasting/retrospective studies are useful to test modeller assumptions, they are subject to a plethora of uncertainties that cannot be easily reduced without strong empirical evidence. Essentially, the usefulness of hindcasting is limited by the availability and fineness of historical energy system data, which usually has very limited temporal and spatial resolution. These dimensions matter a lot when it comes to calculating prices, system resilience and the viability of renewable technologies.

Please be careful with hindcasting studies that make assertions about the past since it is difficult to distinguish between parametric, structural and behavioural uncertainties.

For more on the topic of model evaluation and past uncertainty, see the following:
- Oreskes: [Evaluation (not validation) of quantitative models](https://doi.org/10.1289/ehp.98106s61453)
- Oreskes et al.: [Verification, Validation, and Confirmation of Numerical Models in the Earth Sciences](https://www.jstor.org/stable/2883078)
- Wilson et al.: [Evaluating process-based integrated assessment models of climate change mitigation](https://doi.org/10.1007/s10584-021-03099-9)
- Rowe: [Understanding Uncertainty](https://doi.org/10.1111/j.1539-6924.1994.tb00284.x)

For examples of hindcasting studies, see:
- Chaturvedi et al.: [Model evaluation and hindcasting: An experiment with an integrated assessment model](https://doi.org/10.1016/j.energy.2013.08.061)
- Glotin et al.: [Prediction is difficult, even when it's about the past: A hindcast experiment using Res-IRF, an integrated energy-economy model](https://doi.org/10.1016/j.eneco.2019.07.012)
- Fujimori et al.: [Global energy model hindcasting](http://dx.doi.org/10.1016/j.energy.2016.08.008)


# Features currently in development
The passenger sector has been deactivated while time resolution, storage and weather synchronicity are fixed.
This is to enable easier tests on the impact on runtime these features will have, and for quicker testing.

To do list:
- Rework time slicing by adding a day index and day-indexed representativeness parameter.
- Lenient gets should fail if the parameter is not defined anywhere.
- Fix the D-EXPANSE "double retirement" glitch.
- Fix load profile issues in D-EXPANSE files (incorrect indexes, incompleteness).
- Add k-means plotting functionality to help identify the ideal number of representative days. See https://realpython.com/k-means-clustering-python/
- Fix lack of demand/weather synchronicity in pre-runs (inherited from D-EXPANSE).
- Improve storage by implementing the technique developed by Kotzur et al. (https://doi.org/10.1016/j.apenergy.2018.01.023)
- Cost functions should be set for each sector module, not in the notebook.
- Complete the documentation of all modules.