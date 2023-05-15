**init_activity**: initialize the model's activity. Supports technology deactivation.

$$\forall_{e,y} \quad  \mathrm{TotalAnnualAct}_{e,y} = \begin{cases}
&0 \quad &\text{if } y < \mathbf{ENABLEYR}_{e} \\
&\mathbf{ACTUALACT}_{e,y0} \quad &\text{if } y = \mathbf{ENABLEYR}_{e} = Y_{0}\\
&\text{Free} & \text{otherwise}
\end{cases}$$

>[!important] Setting activity levels in $Y_{0}$
>I do not think this is good practice since it can mislead readers into thinking that the initial year was a model output. I prefer to let the model run for its entire time-span and compare historical observations from the start to ensure users see how adequate the model calibration is (most hindcasting studies do this). 
>
>This setting is here for compatibility with D-EXPANSE, and it can be easily deactivated.

**init_capacity**: initialize the model's capacity in $Y_{0}$. For $Y_{0}$, it can be thought of as a check to ensure the user set the residual capacity ($\mathbf{RESCAP}$) correctly.

$$\forall_{e,y} \quad  ctot_{e,y} = \begin{cases}
&0 \quad &\text{if } y < \mathbf{ENABLEYR}_{e} \\
&\mathbf{ACTUALCAP}_{e,y0} \quad &\text{if } y = \mathbf{ENABLEYR}_{e} = Y_{0}\\
&\text{Free} & \text{otherwise}
\end{cases}$$
