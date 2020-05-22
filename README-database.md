# Creating your own metadata database

We store all of the interesting information associated with each input genome in a relational database that **pathospot-compare** incorporates into the analysis. Additional data providing epidemiological context, such as microbiology test results for non-sequenced specimens, and patient movements through the hospital system, are also stored here. It cannot be underemphasized [how vital the contextual metadata are][natmic] when creating hypotheses based on outbreak phylogenies.

[natmic]: https://www.nature.com/articles/s41564-020-0738-5

The [example dataset (tar.gz)](https://pathospot.org/data/mrsa.tar.gz) includes `mrsa.db`, which is an [SQLite] database. SQLite is a free and widely used database format, with many open source GUI tools available (see below). The easiest way to create an metadata database for your own specimens is to open ours up and modify the data inside, using the same tables and column names.

[SQLite]: https://www.sqlite.org/index.html

Below, we answer the most frequently asked questions about this database, and then provide some formal documentation on our database schema.

## FAQ

### Do I need to be a programmer (or know SQL) to modify the database?

You do not! There are many free graphical tools for working with SQLite databases. Some free options are [DBBrowser](https://sqlitebrowser.org/) and [SQLiteStudio](https://sqlitestudio.pl/) which run on all platforms. Paid options include [Base](https://menial.co.uk/base/) for Mac,  [SQLiteFlow](https://www.sqliteflow.com/) for Mac & iOS, and [Navicat](https://www.navicat.com/en/products/navicat-premium) for all platforms.

### What is `eRAP_ID`?

Most of our columns have fairly transparent naming, but this one unfortunately does not. This column is an (anonymized) patient identifier. You will find this column in the `tIsolates`, `tIsolateTests`, and `tPatientEncounter` tables. Each patient in your dataset should be assigned a unique integer ID.

### What are valid values for `encounter_type`?

This column is seen in the `tPatientEncounter` table, which tracks patient movements during healthcare visits. It is a free text field and you can put whatever you like in this column. However, the special value "Hospital Encounter" indicates an inpatient visit. Note that our definition of inpatient visits includes patients that present to an emergency department and are discharged from there.

### How does `IN_QUERY` work?

When running the rake tasks described in the [main README](https://github.com/powerpak/pathospot-comparison), an environment variable called `IN_QUERY` is expected. This is used as an `SQL WHERE` clause to filter assemblies that are included in the analysis.  Because a LEFT JOIN is performed, you filter by any of the columns in the `tAssemblies`, `tExtracts`, `tStocks`, `tIsolates`, `tOrganisms` and `tHospitals` tables.

In the example analysis, we use `1=1` which performs no such filtering, but you will likely become find it useful to filter by species, location, and/or time range for your own analyses. For example, assuming you continue to use `tOrganisms` as intended, an `IN_QUERY` of `taxonomy_ID=1280` would restrict your analysis to only isolates containing _S. aureus_.
