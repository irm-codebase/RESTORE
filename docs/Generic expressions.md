These are defined globally, and do not create constraints or additional variables. Specific entity modules may override these if necessary.

# Activity expressions

**Total annual activity**: an entity's total annual activity.

$$\forall_{e,y} \quad \mathrm{TotalAnnualAct_{e,y}} = \sum\limits_{d} \mathbf{DL_{y,d}} \sum\limits_{h} \mathbf{HL}\ a_{e,y,d,h}$$

**Hourly capacity to activity**: defines maximum hourly nominal activity. Skipped if an entity has no capacity.

$$\forall_{e,y} \quad \mathrm{HourlyC2A_{e,y}} = \frac{\mathbf{C2A_{e,y}}\ \mathbf{HL}}{365*24}$$

# Cost expressions

**cost_investment**: the investment cost of an entity throughout the model runtime. Skipped in an entity has no capacity.

$$\forall_{e} \quad \mathrm{CostInv_{e}}=\sum\limits_{y} \mathbf{DISC_{y}} \ \mathbf{CINV_{e,y}} \ cnew_{e,y}$$

**cost_fixed_om**: the fixed operation and maintenance cost of an entity through the model runtime. Skipped if an entity has no capacity.

$$\forall_{e} \quad \mathrm{CostFixedOM_{e}} = \sum\limits_{y} \mathbf{DISC_{y}} \ \mathbf{CFIXOM_{e,y}} \ ctot_{e,y}$$

**cost_variable_om**: the variable operation and maintenance cost of an entity through the model runtime.

$$\forall_{e} \quad \mathrm{CostVarOM_{e}} = \sum\limits_{y} \mathbf{DISC_{y}} \ \mathbf{CVAROM_{e,y}} \ \mathrm{TotalAnnualAct_{e,y}} $$

**cost_combined**: sum of all the costs of an entity.

$$\forall_{e} \quad \mathrm{CostCombined_{e}} = \mathrm{CostInv_{e}} + \mathrm{CostFixedOM_{e}} + \mathrm{CostVarOM_{e}}$$
