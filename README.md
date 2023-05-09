# RESTORE model
RESTORE	Retrospective Energy System opTimisation mOdel foR switzErland

# IMPORTANT!
The passenger sector has been deactivated while time resolution, storage and weather synchronicity are fixed.
This is to enable easier tests on the impact on runtime these features will have, and for quicker testing.

To do list:
- Add state of charge for: storage module (i.e., remove D-EXPANSE 'resistor' formulation) and for EVs (needs charge profile)
- Rework time slicing. Choose between year slices (OSeMOSYS) or representative days (MESSAGEix, old D-EXPANSE)
- Fix lack of demand/weather synchronicity (this is an issue inherited from D-EXPANSE, perhaps use a separate module for pre-run clustering?)
- Cost functions should be set for each sector module, not in the notebook.
- Complete the documentation of all modules.