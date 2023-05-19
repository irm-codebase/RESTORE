# Sets

## Variable sets

| Name   | Set | Symbol | Description                                                                                                                                                                                                    |
| ------ | --- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Flow   | $F$ | $f$    | An energy flow such as electricity, heat, fuel, etc. Can be thought of as an equivalent of a "bus" in power systems.                                                                                           |
| Entity | $E$ | $e$    | An element that extracts, converts or uses energy. Has several sub-classes. Each entity can have a theoretical infinite number of inputs and/or outputs.                                                       |
| Year   | $Y$ | $y$    | Year slice within the model run.                                                                                                                                                                                               |
| Day    | $D$ | $d$    | Representative day of the run. These may not be sequential depending on the representative day aggregation algorithm used. It is also possible to represent periods longer than a day (48 hours, a week, etc). |
| Hour   | $H$ | $h$    | Time-slice within each representative day. Usually 1 hour, but users can choose finer or coarser lengths (2 hours, 6, 12, etc).                                                                                |

## Graph sets

| Name    | Set        | Description                             | Code example (m = model)         |
| ------- | ---------- | --------------------------------------- | -------------------------------- |
| Inflow  | $FIE_{f}$  | Entity inflows flowing out of flow $f$. | `for (fx,e) in m.FiE if fx == f` |
| Outflow | $FOE_{f}$  | Entity outflows flowing into flow $f$.  | `for (fx,e) in m.FoE if fx == f` |
| Input   | $EIN_e$    | Input flows of entity $e$.              | `for (f,ex) in m.FiE if ex == e` |
| Output  | $EOUT_{e}$ | Output flows of entity $e$.             | `for (f,ex) in m.FoE if ex == e` |

RESTORE uses a subset of the cartesian product of Flows and Entities to minimise the size of model variables. The model Sets `model.FxE`, `model.FoE` and `model.FiE` are key to this. These sets contain the graph nodes and links exclusively, omitting non-existent connections.

As a brief example, picture a model with 12 Flows, 25 Entities, 30 Years, 2 Days, and 24 Hours. Let's assume that `var` uses all sets:

```python
model.var_bad = pyo.Var(model.F, model.E, model.Y, model.D, model.H)
model.var_good = pyo.Var(model.FxE, model.Y, model.D, model.H)
```

Both variables have the same function, but their sizes differ significantly:

```
var_bad : Size=432000, Index=var_bad_index
var_good : Size=53280, Index=var_good_index
```

For more information, see the following:

https://github.com/brentertainer/pyomo-tutorials/blob/master/intermediate/05-indexed-sets.ipynb

## Other Sets

These sets are for general utility purposes.

| Name            | Set    | Symbol | Description                             |     |                                                                |
| --------------- | ------ | ------ | --------------------------------------- | --- | -------------------------------------------------------------- |
| All years | $YALL$ | $yx$   | An ordered set of years between $Y_{0}, \| Y   \|$ (i.e., one year jumps). Used to fetch inter year-slice data. | 

## Parameters

Important parameters used throughout the model.

| Name        | Symbol              | Description                                                                 |
| ----------- | ------------------- | --------------------------------------------------------------------------- |
| Day length  | $\mathbf{DL_{y,d}}$ | Total number of days represented by each representative day, for each year. |
| Hour length | $\mathbf{HL}$ | Total number of hours represented by each time-slice. Usually 1.            |