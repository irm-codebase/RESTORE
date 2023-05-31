Group identifier: `_convpass_`

>**Important**: this file describes unique functions in the module. To see the generic constraints used by the module, please see the code.


The passenger sector represents represents transport of people. Entities are specific transport technologies (cars, buses, etc.), 
with their input being one or several energy flows (either fuel or electricity), their activity being defined as vehicle kilometres travelled (vkm), and their outputs defined in passenger kilometres travelled (pkm).

For now, only two types of travel are described in the model (short, long), each with their specific speeds. However, more specific travel ranges can be easily set up.

```mermaid
flowchart LR
    C{elec.} --> |fin, TWh|D((train))
    A{diesel} --> |fin, TWh|B((bus))
    A --> |fin, TWh|F
    E{petrol} --> |fin, TWh|F((car))
    
    D --> |fout, pkm, long|G{Travel}
    B --> |fout, pkm, short|G
    F --> |fout, pkm, short|G
    F --> |fout, pkm, long|G
```

# Constraints  

**travel_time_budget**: Limit the available time for travel each year based on the average time each person travels in a day ($\mathbf{TRAVELTIME}$).
See Daly et al. 2014. 10.1016/j.apenergy.2014.08.051 for more information.

$$\forall_{y} \quad 365\cdot\mathbf{POPUL_{y} \cdot TRAVELTIME_{y}} \ge 10^{6} \cdot  \sum\limits_{e \in Passenger} \sum\limits_{f \in EOUT_{e}} \frac{\mathrm{TotalAnnualOutflow_{f,e,y}}}{\mathbf{SPEED_{f,e,y}}}$$
