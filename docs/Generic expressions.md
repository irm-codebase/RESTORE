These are defined globally, and do not create constraints or additional variables. Specific entity types may override these if necessary.

# Activity expressions

**Total annual activity**: an entity's total annual activity.

$$\forall_{e,y} \quad \mathrm{TotalAnnualAct}_{e,y} = \sum\limits_{d} \mathbf{DL}_{y,d} \sum\limits_{h} \mathbf{HL}\ a_{e,y,d,h}$$

**Hourly capacity to activity**: defines maximum hourly nominal activity. Skipped if an entity has no capacity.

$$\forall_{e,y} \quad \mathrm{HourlyC2A}_{c,y} = \frac{\mathbf{C2A}_{c,y}\ \mathbf{HL}}{365}$$

# Cost expressions

**cost_investment**: the investment cost of an entity throughout the model runtime. Skipped in an entity has no capacity.

$$\forall_{e} \quad \mathrm{CostInv}_{e}=\sum\limits_{y} \mathbf{DR}_{y} \ \mathbf{CINV}_{e,y} \ cnew_{e,y}$$

**cost_fixed_om**: the fixed operation and maintenance cost of an entity through the model runtime. Skipped if an entity has no capacity.

$$\forall_{e} \quad \mathrm{CostFixedOM}_{e} = \sum\limits_{y} \mathbf{DR}_{y} \ \mathbf{CFIXOM}_{e,y} \ ctot_{e,y}$$

**cost_variable_om**: the variable operation and maintenance cost of an entity through the model runtime.

$$\forall_{e} \quad \mathrm{CostVarOM}_{e} = \sum\limits_{y} \mathbf{DR}_{y} \ \mathbf{CVAROM}_{e,y} \ \mathrm{TotalAnnualAct}_{e,y} $$

**cost_combined**: sum of all the costs of an entity.

$$\forall_{e} \quad \mathrm{CostCombined}_{e} = \mathrm{CostInv}_{e} + \mathrm{CostFixedOM}_{e} + \mathrm{CostVarOM}_{e}$$
