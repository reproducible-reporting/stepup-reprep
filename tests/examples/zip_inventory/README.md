ZIP files in RepRep are created by first preparing a inventory file, which lists all files to be
zipped with their expected size and Blake2b hexdigest.
This offers an extra level of validation before preparing an archive, which is often one of the last steps.
The inventory files can also be used for later validation of the contents of the ZIP file.
