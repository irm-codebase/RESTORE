# Important notes!!!!!!!!

This math is not up to date in this version of the model. It will be updated before a main release of the software.

The set notation of this could be improved. Specifically for $\sum\limits$, you should specify that f in the intersection of F and FIE, for example. Also, $p$ needs to be changed to $e$.

# Objective function

$$Min \quad \sum\limits CostInv+CostFixedOM + CostVar - RevVar$$
where:
$$\begin{align*}
CostInv &= \sum\limits_{y \in Y} \sum\limits_{p \in P} \mathbf{DR}_{y}\   \mathbf{CINV}_{p,y}\ cnew_{p,y}\\
CostFixedOM &= \sum\limits_{y \in Y} \sum\limits_{p \in P} \mathbf{DR}_{y}\ \mathbf{CFOM}_{p,y} \ ctot_{p,y}\\
CostVar &= \sum\limits_{y \in Y} \sum\limits_{h \in H} \left(\sum\limits_{p \in G \cup C \cup S} \mathbf{DR}_{y}\ \mathbf{CVAR}_{p,y} \ a_{p,y,h} + \sum\limits_{p \in I} \mathbf{DR}_{y}\ \mathbf{CIMP}_{p,y} \ aimp_{p,y,h}\right)\\
RevVar &= \sum\limits_{y \in Y} \sum\limits_{h \in H} \sum\limits_{p \in I} \mathbf{DR}_{y}\ \mathbf{REXP}_{p,y} \ aexp_{p,y,h}
\end{align*}$$

# Y0
Processes:
$$\begin{align*}
&\text{convacty0}: &\forall p \in C \quad \sum\limits_{h \in H} a_{p,y_{0}, h} &= \mathbf{A}_{p,y_{0}}\\
&\text{stoacty0}: &\forall p \in S  \quad  \sum\limits_{h \in H} a_{p,y0,h} &= \mathbf{A}_{p,y_{0}}\\
&\text{impacty0}: &\forall p \in I  \quad  \sum\limits_{h \in H} aimp_{p,y0,h} &= \mathbf{AI}_{p,y_{0}}\\\\
&\text{expacty0}: &\forall p \in I  \quad  \sum\limits_{h \in H} aexp_{p,y0,h} &= \mathbf{AE}_{p,y_{0}}\\
\end{align*}$$
Capacities:
$$\begin{align*}
\text{ctoty0}: \forall p \in P \begin{cases}
ctot_{p,y_{0}} &= \mathbf{CTOT}_{p,y_{0}} \quad &\text{if enabled}\\
\text{Skip} \quad &&\text{otherwise}
\end{cases}\\
\text{cnewy0}: \forall p \in P \begin{cases}
cnew_{p,y_{0}} &= \mathbf{CNEW}_{p,y_{0}} \quad &\text{if enabled}\\
\text{Skip} \quad &&\text{otherwise}
\end{cases}\\
\text{crety0}: \forall p \in P \begin{cases}
cret_{p,y_{0}} &= \mathbf{CRET}_{p,y_{0}} \quad &\text{if enabled}\\
\text{Skip} \quad &&\text{otherwise}
\end{cases}\\

\end{align*}$$

# Input - Output

I/O balance:
$$\text{inoutbalance}: \quad \forall f, y, h \in F,Y,H \quad \sum\limits_{e \in f \cap FOE} fout_{f,e,y,h} = \sum\limits_{e \in f \cap FIE}fin_{f,e,y,h}$$

Inflow (sum/mux):  ^842b68
$$\begin{align*}\text{flowin}: \quad &\forall p \in P \setminus I ,y,h \in Y,H \quad &\sum\limits_{f \in FIE | p \in FIE}\boldsymbol{\eta }\mathbf{I}_{f,p,y,h}\cdot fin_{f,p,y,h} = a_{p,y,h}\\
&\forall p \in I ,y,h \in Y,H \quad &\sum\limits_{f \in FOE | p \in FOE}\boldsymbol{\eta }\mathbf{I}_{f,p,y,h}\cdot fin_{f,p,y,h} = aexp_{p,y,h}
\end{align*}$$

^95f5da

Outflow (separate/demux): ==This function might change to make the output flexible...==
$$\begin{align*}&\text{flowout}:\\
&\forall f,e \in FOE,\ y,h \in Y,H \begin{cases}
\boldsymbol{\eta }\mathbf{O}_{f,e,y,h}\cdot a_{e,y,h} = fout_{f,e,y,h}\quad \text{if } e \ni I\\
\boldsymbol{\eta }\mathbf{O}_{f,e,y,h}\cdot aimp_{e,y,h} = fout_{f,e,y,h}\quad \text{if } e \in I
\end{cases}
\end{align*}$$

^ea8ae6

Max shares at flow: ==outputs must be in the same units!!!==
$$\begin{align*}
&\text{maxinflowshare: } \\
&\forall f,p\in FIE, \ y,h\in Y,H \begin{cases}
fin_{f,p,y,h} ≤ \mathbf{MXIFS}_{f,p} \sum\limits_{e \in FIE | f \in FIE}fin_{f,e,y,h} \quad &\text{if } \mathbf{EMXIFS}_{f,p} > 0\\
\text{Skip} & \text{otherwise}
\end{cases}
\end{align*}$$

^8f61c5

$$\begin{align*}&\text{maxoutflowshare: } \\
&\forall f,p\in FOE, \ y,h\in Y,H \begin{cases}
fout_{f,p,y,h} ≤ \mathbf{MXOFS}_{f,p} \sum\limits_{e \in FOE | f \in FOE}fout_{f,e,y,h} \quad &\text{if } \mathbf{EMXOFS}_{f,p} > 0\\
\text{Skip} & \text{otherwise}
\end{cases}
\end{align*}$$

^a1d207

# Demand
**Only one demand per final flow!**
$$\text{dem}: \forall f,d\in F \cap FIE|D \cap FIE,\ y,h \in Y,H \quad fin_{f,d,y,h}=\mathbf{DEM}_{d,y,h}$$

# Capacity

For all the following:
- $P \in E \setminus D$
- Activated when, for $p \in P$, $\mathbf{ECAP}_{p} > 0$
- Skipped via `Constraint.Skip` otherwise

Maximum capacity:
$$\text{capmax}:\quad \forall{p \in P, y \in Y} \quad ctot_{p, y} ≤ \mathbf{CMAX}_{p}$$
Capacity transfer:
$$\text{captrans}:\quad \forall{p \in P, y \in Y \setminus Y_{0}} \quad ctot_{p,y} = ctot_{p,y-1} + cnew_{p,y} - cret_{p,y}$$

Capacity retirement:
$$\begin{align*}
&\text{capret}:\\
&\forall p,y \in P,Y \setminus Y_0 \quad \begin{cases}
cret_{p,y}&= \mathbf{RCAP}_{p,y} \quad &\text{if } \mathbf{LIFE}_{p}>y-Y_{0}\\
cret_{p,y} &= \mathbf{RCAP}_{p,y}+cnew_{p,y-\mathbf{LIFE_{p}}} &\text{if } \mathbf{LIFE}_{p}≤y-Y_{0}\\
cret_{p,y} &= 0 &\text{if } \mathbf{LIFE}_{p} \text{ is None}
\end{cases}
\end{align*}$$
Build rate:
$$\text{capbuildrate}: \quad \forall p,y \in P,Y \quad \begin{cases}
&cnew_{p,y} ≤ \mathbf{BR}_{p} \quad &\text{if } \mathbf{BR}_{p} \text{ is not None} \\
&Skip &\text{otherwise}
\end{cases}$$

# Activity constraints

Ramping: 
For trade, full flexibility is assumed so it is excluded by default.
$$\begin{align*}
&\text{rampup}:\quad \forall p,y,h \in P \setminus I, Y, H \setminus H_{0} \quad &\begin{cases}
a_{p,y,h} - a_{p,y,h-1}&≤ \mathbf{RAMP}_{p}\ ctot_{p,y} \quad &\text{if } \mathbf{RAMP}_{p} < 1 \\
Skip && \text{otherwise}
\end{cases}\\
&\text{rampdown}:\quad \forall p,y,h \in P \setminus I, Y, H \setminus H_{0} \quad &\begin{cases}
a_{p,y,h-1} - a_{p,y,h}&≤ \mathbf{RAMP}_{p}\ ctot_{p,y} \quad &\text{if } \mathbf{RAMP}_{p} < 1 \\
Skip && \text{otherwise}
\end{cases}\\
\end{align*}$$

Maximum annual activity:
Separate limits for imports and exports are permitted.
$$
\begin{align*}
\text{actmax}: \quad &\forall p, y \in P \setminus I, Y \quad \begin{cases}
\mathbf{TP}\sum\limits_{h \in H}a_{p,y,h}≤\mathbf{AMAX}_{p}\quad \text{if }\mathbf{AMAX}_{p} &\text{ is not None}\\
Skip & \text{otherwise}
\end{cases}\\
\text{actmaximp}:\quad  &\forall p, y \in P \setminus I, Y \quad \begin{cases}
\mathbf{TP}\sum\limits_{h \in H}aimp_{p,y,h}≤\mathbf{AMAX}_{p}\quad \text{if }\mathbf{AMAX}_{p} &\text{ is not None}\\
Skip & \text{otherwise}
\end{cases}\\
\text{actmaxexp}:\quad  &\forall p, y \in P \setminus I, Y \quad \begin{cases}
\mathbf{TP}\sum\limits_{h \in H}aexp_{p,y,h}≤\mathbf{AMAX}_{p}\quad \text{if }\mathbf{AMAX}_{p} &\text{ is not None}\\
Skip & \text{otherwise}
\end{cases}
\end{align*}
$$

Maximum annual activity capacity:
Equivalent to the sum of the total yearly activity vs total annual capacity (fitted to number of modelled days instead of whole year, it is the same thing).
Useful to detect capacity issues in $Y_{0}$. ==Might be unnecessary? but why does D-EXPANSE fail to catch this?==
$$\text{maxannualactcap}: \quad \forall p,y \in P \setminus I, Y \quad\begin{cases}
\sum\limits_{h \in H}a_{p,y,h} ≤ \mathbf{NDAY}\cdot \mathbf{LFMAX}_{p,y}\ ctot_{p,y} \quad \text{if } p \ni CVRE\\
\sum\limits_{h \in H}a_{p,y,h} ≤ \mathbf{NDAY}\cdot \overline{ \mathbf{LFVRE}}_{p,y}\ ctot_{p,y} \quad \text{if } p \in CVRE
\end{cases}$$
$$\text{maxannualactcap}: \quad \forall p,y \in I, Y \quad
\sum\limits_{h \in H}aimp_{p,y,h}+aexp_{p,y,h} ≤ \mathbf{NDAY}\cdot \mathbf{LFMAX}_{p,y}\ ctot_{p,y}$$

Load Factors:
In the case of exports, $aimp/aexp$ will  be set to 0 if imports/exports are disabled (or throw an error if none are enabled while capacity is active).
$$
\begin{align*}
&\text{lfmin/max}: \\
&\forall p,y,h \in P \setminus I, Y, H \ \begin{cases}
\mathbf{LFMIN}_{p,y}\ ctot_{p,y}≤a_{p,y,h}≤\mathbf{LFMAX}_{p,y}\ ctot_{p,y}\quad \text{if } p \ni CVRE\\
\mathbf{LFMIN}_{p,y}\ ctot_{p,y} ≤ a_{p,y,h}≤\mathbf{LFVRE}_{p,y,h}\ ctot_{p,y} \quad \text{if } p \in CVRE
\end{cases}\\
&\text{tradelfmin/max}: \\
&\forall p,y,h \in I, Y, H \quad
\mathbf{LFMIN}_{p,y}\ ctot_{p,y} ≤ aimp_{p,y,h}+aexp_{p,y,h}≤\mathbf{LFMAX}_{p,y}\ ctot_{p,y}\\
\end{align*}
$$

# Flow constraints

Peak capacity demand: 
$$\text{peakcapdem}:\forall f, y \in F, Y \begin{cases}
\sum\limits_{e \in FOE |f \in FOE}\boldsymbol{\eta}\mathbf{O}_{p, f}\mathbf{RO}_{p,f}\mathbf{PK}_p\ ctot_{p,y}≥(1+\mathbf{CM}_f)\mathbf{PKCD}_{f,y} &\text{if enabled}\\
Skip &\text{otherwise}\\
\end{cases}$$
Base capacity demand: ==currently the use of LFMIN  = 0 in y0 is causing issues here==
$$
\text{basecapdem}:\forall f,y, \in F,Y\begin{cases}
\begin{align*}
\sum\limits_{e \in FOE \setminus I | f \in FOE} (\boldsymbol{\eta}\mathbf{O}_{p, f}\mathbf{RO}_{p,f}\mathbf{LFMIN}_{p,y}\ ctot_{p,y})-\\
\sum\limits_{e \in FOE \cap I | f \in FOE}(\boldsymbol{\eta}\mathbf{O}_{p, f}\mathbf{RO}_{p,f}\mathbf{LFMIN}_{p,y}\ ctot_{p,y})
\end{align*}≤ \mathbf{BSCD}_{f,y} &\text{if enabled} \\
Skip & \text{otherwise}
\end{cases}
$$
