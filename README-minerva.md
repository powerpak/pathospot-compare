## Getting started on Minerva/Chimera (Mount Sinai users)

The pipeline can also access all required software using the module system on Chimera nodes in the [Minerva cluster](https://labs.icahn.mssm.edu/minervalab/). Clone this repository to a directory and `cd` into it. First run the following to set up required Ruby gems and a new conda environment:

    $ scripts/example.MINERVA.prepare-conda.sh

You'll then want to configure your environment:

    $ cp scripts/example.MINERVA.env.sh scripts/env.sh  

The defaults should work for any Minerva user, although you will want to adjust `PATHOGENDB_URI` with the correct MySQL connection string. Then, you can source the script into your shell, which sets up and activates a conda environment ready to run the pipeline:

    $ source scripts/env.sh

When this is complete, you should be able to continue with the steps under [**Usage** in the main README](https://github.com/powerpak/pathospot-compare#usage#usage).