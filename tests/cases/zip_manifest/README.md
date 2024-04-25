ZIP files in RepRep are created by first preparing a manifest file, which lists all files to be
zipped with their expected size and Blake2b hexdigest.
This offers an extra level of validation before preparing an archive, which is often one of the last steps.
The manifest files can also be used for later validation of the contents of the ZIP file.
