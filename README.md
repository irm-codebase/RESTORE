# The RESTORE model
RESTORE: RetrospEctive SecTor cOupled eneRgy toolsEt (tentative name)

## A bit of history
RESTORE is based on D-EXPANSE, a stylized national-level nodal power system model used in hindcasting studies:
- Trutnevyte: [Does cost optimization approximate the real-world energy transition?](http://dx.doi.org/10.1016/j.energy.2016.03.038)
- Wen et al.: [Accuracy indicators for evaluating retrospective performance of energy system models](https://doi.org/10.1016/j.apenergy.2022.119906)
- Wen et al.: [Hindcasting to inform the development of bottom-up electricity system models: The cases of endogenous demand and technology learning](https://doi.org/10.1016/j.apenergy.2023.121035)

**Important:** 
D-EXPANSE is not the same model as EXPANSE, which is a spatially explicit electricity model with no inter year slicing!
You can learn more about EXPANSE in these studies:
- Sasse et al.: [Distributional trade-offs between regionally equitable and cost-efficient allocation of renewable electricity generation](https://doi.org/10.1016/j.apenergy.2019.113724)
- Sasse et al.: [Regional impacts of electricity system transition in Central Europe until 2035](https://doi.org/10.1038/s41467-020-18812-y)
- Sasse et al.: [A low-carbon electricity sector in Europe risks sustaining regional inequalities in benefits and vulnerabilities](https://doi.org/10.1038/s41467-023-37946-3)

## New features in RESTORE
RESTORE builds on D-EXPANSE by implementing:
- Graph-based flows
- Spatial disaggregation
- Sector coupling functionality
- Reworked architecture to improve readability and modularity
- Generic, pre-made constraints and expressions that can be easily re-used in sector modules defined by developers

RESTORE also features a fully standardized prototyping workflow based on [FAIR principles](https://www.go-fair.org/fair-principles/). Model components (called "entities") are defined in single files, where the user can specify parameter names, values, units and sources. These files are rapidly converted into a single configuration file that the model uses as input. Conversion of currencies, energy units and power units is also integrated into this process.

This lets model developers track the sources of their data, and gives users and other researchers full transparency into the model's operation and assumptions.

## Features currently in development

- Implement an option for imperfect foresight.
    - Variable foresight length.
    - Variable length of years saved in each run.
- Cycle flow constraints in the energy transmission module.
    - Based on Kirchhoff formulation developed by Hörsch et al.
    - Also implemented in EXPANSE.
    - See https://doi.org/10.1016/j.epsr.2017.12.034
- Seasonal storage capacity expansion.
    - Implement the algorithm developed by Kotzur et al.
    - Allow users to choose between cyclic storage and seasonal storage constraints.
    - See https://doi.org/10.1016/j.apenergy.2018.01.023
- Improve representative day algorithm.
    - Ensure weather synchronicity (PV, Wind and Hydro run-off).
    - Create cnf file standard for hourly data series in representative days. Must be searchable by entity_id.
    - Add options for different types of clustering algorithm (k-means, spectral, etc).

# IMPORTANT

Although hindcasting/retrospective studies are useful to test modeller assumptions, they are subject to a plethora of uncertainties that are difficult to avoid. Essentially, their usefulness is limited by the availability and fineness of historical energy system data, which worsens the further to the past you go and the more specific your data requirements are. Temporal and spatial resolution matter a lot when it comes to calculating prices, system resilience and the viability of renewable technologies. 

Due to this, I would argue that RESTORE is ***not*** a validation tool, but rather a useful test-bench to evaluate features before they are added to more complex models.

For more on the topic of model evaluation and past uncertainty, see the following:
- Oreskes: [Evaluation (not validation) of quantitative models](https://doi.org/10.1289/ehp.98106s61453)
- Oreskes et al.: [Verification, Validation, and Confirmation of Numerical Models in the Earth Sciences](https://www.jstor.org/stable/2883078)
- Wilson et al.: [Evaluating process-based integrated assessment models of climate change mitigation](https://doi.org/10.1007/s10584-021-03099-9)
- Rowe: [Understanding Uncertainty](https://doi.org/10.1111/j.1539-6924.1994.tb00284.x)

For examples of hindcasting studies, see:
- Chaturvedi et al.: [Model evaluation and hindcasting: An experiment with an integrated assessment model](https://doi.org/10.1016/j.energy.2013.08.061)
- Glotin et al.: [Prediction is difficult, even when it's about the past: A hindcast experiment using Res-IRF, an integrated energy-economy model](https://doi.org/10.1016/j.eneco.2019.07.012)
- Fujimori et al.: [Global energy model hindcasting](http://dx.doi.org/10.1016/j.energy.2016.08.008)
