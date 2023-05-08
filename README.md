# RESTORE model
RESTORE	Retrospective Energy System opTimisation mOdel foR switzErland

To do list:
- Modify capacity constraints to include vintaging (i.e., no more D-EXPANSE capacity constraints)
- Add state of charge for: storage module (i.e., remove D-EXPANSE 'resistor' formulation) and for EVs (needs charge profile?)
- Rework time slicing. Choose between year slices (OSeMOSYS) or representative days (MESSAGEix, old D-EXPANSE??)
- Fix lack of demand/weather synchronicity (issue inherited from D-EXPANSE, perhaps use a separate module for pre-run clustering?)