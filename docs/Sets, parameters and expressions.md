# Sets

Variable sets

| Name   | Symbol | Set | Description                                                                                                          |
| ------ | ------ | --- | -------------------------------------------------------------------------------------------------------------------- |
| Flow   | $f$    | $F$ | An energy flow such as electricity, heat, fuel, etc. Can be thought of as an equivalent of a "bus" in power systems. |
| Entity | $e$    | $E$ | An element that extracts, converts or uses energy. Has several sub-classes.                                          |
| Year   | $y$    | $Y$ | Year of the run.                                                                                                     |
| Day    | $d$    | $D$ | Representative day of the run. Not necessarily in sequential order.                                                  |
| Hour   | $h$    | $H$ | Time-slice within each representative day.                                                                           |

Graph sets

| Name    | Set        | Description                             |
| ------- | ---------- | --------------------------------------- |
| Outflow | $FOE_{f}$  | Entity outflows flowing into flow $f$.  |
| Inflow  | $FIE_{f}$  | Entity inflows flowing out of flow $f$. |
| Input   | $EIN_e$    | Input flows of entity $e$.              |
| Output  | $EOUT_{e}$ | Output flows of entity $e$.             | 

# Parameters

Important parameters used throughout the model.

| Name        | Symbol              | Description                                                                 |
| ----------- | ------------------- | --------------------------------------------------------------------------- |
| Day length  | $\mathbf{DL}_{y,d}$ | Total number of days represented by each representative day, for each year. |
| Hour length | $\mathbf{HL}$ | Total number of hours represented by each time-slice. Usually 1.            | 
