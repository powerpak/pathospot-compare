# PathogenDB genome comparison

## Requirements

As of now, this only runs on [Minerva](http://hpc.mssm.edu) because it uses modules and software found on that cluster.  In due time, it might be made portable to other systems.

## Usage

First, clone this repository to a directory and `cd` into it.  You'll want to configure your environment first using the included script:

    $ cp scripts/env.example.sh scripts/env.sh
    $ $EDITOR scripts/env.sh    

For the rest of the variables, the defaults should work for any Minerva user.  Then, you can source the script into your shell and install required gems locally into the `vendor/bundle` directory as follows:

    $ source scripts/env.sh
    $ bundle install --deployment

When this is complete, you should be able to run rake to kick off the pipeline as follows. However, also read **[Environment variables](#environment-variables)** below, as certain tasks require more variables to be set before being invoked.

    $ rake -T                    # list the available tasks
    $ rake $TASK_NAME            # run the task named $TASK_NAME
    $ FOO="bar" rake $TASK_NAME  # run $TASK_NAME with FOO set to "bar"

When firing up the pipeline in a new shell, always remember to `source scripts/env.sh` before running `rake`.

### Environment variables

Certain tasks within the pipeline require you to specify some extra information as an environment variable.  You can do this by either editing them into `scripts/env.sh` and re-running `source scripts/env.sh`, or you can prepend them to the `rake` invocation, e.g.:

    $ FOFN= rake pull_down_raw_reads

If a required environment variable isn't present when a task is run and there is no default value, rake will abort with an error message.

Variable             | Required by                           | Default | Purpose
---------------------|---------------------------------------|---------|-----------------------------------
`OUT`                | all tasks                             | ./out   | This is where your interim files are saved.
`IN_FOFN`            | `mugsy` `mauve`                       | (none)  | A file containing filenames that will be processed as input
`OUT_PREFIX`         | `mugsy` `mauve`                       | out     | This prefix will be prepended to output filenames (so you can track files generated for each invocation)
`OUTGROUP`           | `mugsy`                               | (none)  | The [outgroup][] to specify for `RAxML`
`SEED_WEIGHT`        | `mauve`                               | (none)  | Use this seed weight for calculating initial anchors
`LCB_WEIGHT`         | `mauve`                               | (none)  | Minimum pairwise LCB score

[outgroup]: http://en.wikipedia.org/wiki/Outgroup_%28cladistics%29

### Dependency graph

This Rakefile is able to build a dependency graph of its intermediate files from itself.  Use the `rake graph` task for this; it will be generated at `$OUT/pathogendb-comparison.png`.

(TODO)

## Other notes

This pipeline downloads and installs the appropriate versions of Mugsy, Mauve, and RAxML into `vendor/`.
