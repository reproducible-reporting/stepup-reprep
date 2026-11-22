This test does not actually upload data to Zenodo, due to the missing token.
It writes the inventory of the files to upload and validates the config file at every start,
and shows that an offline start does not run the sync merely because StepUp started.
It also shows that `stepup rebuild --recheck` runs the sync again in watch mode, except offline.
