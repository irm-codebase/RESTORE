# RESTORE model
RESTORE	Retrospective Energy System opTimisation mOdel foR switzErland

To do list:
- Modify capacity constraints to include vintaging (i.e., remove D-EXPANSE formulation)
- Add state of charge for: storage module (i.e., remove D-EXPANSE 'resistor' formulation) and for EVs (needs charge profile)
- Rework time slicing. Choose between year slices (OSeMOSYS) or representative days (MESSAGEix, old D-EXPANSE)
- Fix lack of demand/weather synchronicity (this is an issue inherited from D-EXPANSE, perhaps use a separate module for pre-run clustering?)
- Cost functions should be set for each sector module, not in the notebook.