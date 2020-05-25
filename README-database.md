# Creating your own metadata database

We store all of the interesting information associated with each input genome in a relational database that **pathospot-compare** incorporates into the analysis. Additional data providing epidemiological context, such as patient movements and microbiology test results for additional specimens, are also stored here. It cannot be underemphasized [how vital these contextual metadata are][natmic] when attempting to interpret outbreak phylogenies.

[natmic]: https://www.nature.com/articles/s41564-020-0738-5

The [example dataset (tar.gz)](https://pathospot.org/data/mrsa.tar.gz) includes `mrsa.db`, which is an [SQLite] database. SQLite is a free and widely used database format, with many open source GUI tools available (see below). The easiest way to create an metadata database for your own specimens is to open our example and modify the data inside, retaining the same table and column structure.

[SQLite]: https://www.sqlite.org/index.html

Below, we answer the most frequently asked questions, and then provide some formal documentation on the database schema.

## FAQ

### Do I need to be a programmer (or know SQL) to modify the database?

You do not! There are many free graphical tools for working with SQLite databases. Some free options are [DBBrowser](https://sqlitebrowser.org/) and [SQLiteStudio](https://sqlitestudio.pl/) which run on all platforms. Paid options include [Base](https://menial.co.uk/base/) for Mac,  [SQLiteFlow](https://www.sqliteflow.com/) for Mac & iOS, and [Navicat](https://www.navicat.com/en/products/navicat-premium) for all platforms.

However, if you want to automate anything about your database or make use of the `IN_QUERY` parameter, it would be helpful to learn some [basic SQL](https://www.sqlitetutorial.net/).

### How does `IN_QUERY` work?

When running the rake tasks described in the [main README](https://github.com/powerpak/pathospot-comparison), an environment variable called `IN_QUERY` is expected. This is used as an `SQL WHERE` clause to filter the assemblies that will be included.  Since several JOINs are performed during this query, you may reference any of the columns in the [`tAssemblies`](#tassemblies), [`tExtracts`](#textracts), [`tStocks`](#tstocks), [`tIsolates`](#tisolates), [`tOrganisms`](#torganisms) and [`tHospitals`](#thospitals) tables.

In the example analysis, we use `IN_QUERY="1=1"` which performs no filtering at all, but you will likely become find it useful to filter by species, location, and/or time range for your own analyses. For example, assuming you continue to use [`tOrganisms`](#torganisms) as intended, an `IN_QUERY` of `taxonomy_ID=1280` would restrict your analysis to _S. aureus_ isolates only.

### What is `eRAP_ID`?

Most of our columns have fairly transparent naming, but this one unfortunately does not. This column is an (anonymized) patient identifier named after one of our [data warehouses](https://erap.mssm.edu). You will find this column in the [`tIsolates`](#tisolates), [`tIsolateTests`](#tisolatetests), and [`tPatientEncounter`](#tpatientencounter) tables. Each patient in your dataset should be assigned a unique integer ID.

### What are valid values for `encounter_type`?

This column is seen in the [`tPatientEncounter`](#tpatientencounter) table, which tracks patient movements during healthcare visits. It is a free text field and you can put whatever you like in this column. However, the special value "Hospital Encounter" indicates an inpatient visit. Note that our definition of inpatient visits includes patients that present to an emergency department and are discharged from there.

### Do I have to use SQLite?

You do not; you can use any database that [Sequel](https://sequel.jeremyevans.net/rdoc/files/doc/opening_databases_rdoc.html) has an adapter for. If you like MySQL, for instance, you may create a database, edit it with [phpMyAdmin](https://www.phpmyadmin.net/), and then connect to it with a `PATHOGENDB_URI` of the form `mysql2://user:password@host/db_name`.

## Schema

An abbreviated graphical summary of the schema follows (click to see the full version with all fields included).

<a href="https://pathospot.org/images/schema-large.png"><img src="https://pathospot.org/images/schema-compact.png" /></a>

In this schema, the major landmarks are:

- [`tAssemblies`](#tassemblies), which contains metadata on the _sequenced_ isolates and corresponds 1:1 with the FASTA/BED files in `IGB_DIR`--they are linked by `assembly_data_link` which contains the name of the FASTA file and its parent directory.
- [`tIsolates`](#tisolates), which contains metadata on both _sequenced_ and _collected but not sequenced_ isolates, and links them to patients via `eRAP_ID` and locations via `hospital_ID` and `collection_unit`.
- [`tPatientEncounter`](#tpatientencounter), which contains data on patient movements through the hospitals
- [`tIsolateTests`](#tisolatetests), which contains data on microbiology tests for the patients (that may or may not yield isolates, as in [`tIsolates`](#tisolates)).

You may notice that we chain through two intermediary tables, [`tStocks`](#tstocks) and [`tExtracts`](#textracts), to get from [`tAssemblies`](#tassemblies) to their respective [`tIsolates`](#tisolates). This is because we prefer to store the provenance of intermediary steps in our stocking and sequencing process in case they need to be debugged or repeated. If you don't need such detail, you can feel free to use the exact same string for `isolate_ID`, `stock_ID`, `extract_ID`, and `assembly_ID`, and simply create dummy entries in [`tStocks`](#tstocks) and [`tExtracts`](#textracts) for each assembly-isolate pair to link them all together.

### tAssemblies

Rows of this table associate metadata with each of the FASTA _sequences_ that you store in `IGB_DIR`. We call these sequences _assemblies_ because we attempt to assemble complete genomes for all isolates from PacBio long reads, but technically, your sequences can be genome fragments assembled from short reads, [core genomes](http://www.metagenomics.wiki/pdf/definition/pangenome), or smaller sets of housekeeping genes as in [MLST][]. Note that less complete sequences will lead to less optimal alignments and decrease your confidence in distinguishing closely related strains.

[MLST]: http://pubmlst.org/

Fields in this table are:

- `auto_ID` (integer; PK): An autoincrementing ID for this table.
- `extract_ID` (string; FK to [`tExtracts`](#textracts)): the extract that was sequenced to create this assembly.
- `assembly_ID` (string): a string that uniquely identifies this assembly. Can contain `A-Za-z0-9._-`.
- `mlst_subtype` (string): optional. The [MLST][] sequence type for this assembly, if you have it.
- `assembly_data_link` (string): The name of the FASTA file for this sequence (minus the extension), which is also the name of its parent directory within `IGB_DIR`. Like `assembly_ID`, this should also be unique.
- `contig_count` (integer): optional. How many contigs are in your assembly, i.e. how many sequences are in the FASTA file.
- `contig_N50` (integer): optional. The minimum contig length needed to [cover 50% of the genome](http://www.metagenomics.wiki/pdf/definition/assembly/n50), when they are ordered from longest to shortest, i.e. a length weighted median.
- `contig_maxlength` (integer): optional. The length of the longest contig.
- `contig_maxID` (string): optional. The ID of the longest contig.
- `qc_failed` (integer): optional. We set this to a non-zero number if our automatic QC fails on an assembly, so it can be excluded from comparative analysis until it is fixed.

### tExtracts

Before sequencing, we have to extract DNA from a stock, e.g. by pelleting cells and using a [DNA extraction kit](https://www.qiagen.com/lu/products/top-sellers/dneasy-blood-and-tissue-kit/). These extracts are recorded separately in this table, as it may need to be performed multiple times for a stock, e.g., if we need to resequence the same stock multiple times.

Fields in this table are:

- `extract_ID` (string, PK): a unique string that identifies this extract. Can contain `A-Za-z0-9._-`.
- `stock_ID` (string, FK to [`tStocks`](#tstocks)): which stock this extract was created from.

### tStocks

For all isolates produced by our [clinical microbiology lab][cml] that we bank for sequencing, we create one or more frozen stocks. This table tracks the stocks and links them to the isolates they were created from.

Fields in this table are:

- `stock_ID` (string, PK): a unique string that identifies this stock. Can contain `A-Za-z0-9._-`.
- `isolate_ID` (string, FK to [`tIsolates`](#tisolates)): which isolate this stock was created from.

[cml]: https://icahn.mssm.edu/about/departments/pathology/clinical/microbiology/clinical-services)

### tIsolates

This table stores metadata on all isolates produced by our [clinical microbiology lab][cml] that are included in active surveillance programs. At a minimum, you need to provide metadata for isolates that are sequenced and have a corresponding entry in [`tAssemblies`](#tassemblies); however you may also provide metadata on isolates that have been recorded and/or banked but not chosen for sequencing, which will be layered on top of the visualizations.

Typically, isolates are collected from positive clinical microbiology tests (such as blood or urine cultures, aka [`tIsolateTests`](#tisolatetest)) and therefore isolates can (optionally) be associated with entries in [`tIsolateTestResults`](#tisolatetestresults).

Fields in this table are:

- `isolate_ID` (string, PK): a unique string that identifies this isolate. Can contain `A-Za-z0-9_-`.
- `eRAP_ID` (integer): an opaque integer ID for the patient that the isolate was collected from. Every patient should have a unique ID. There is no table enumerating patients and patient-specific data in our schema, as these IDs refer directly to entries in a [clinical data warehouse][erap].
- `organism_ID` (integer; FK to [`tOrganisms`](#torganisms)): the species that was identified for this isolate.
- `hospital_ID` (integer; FK to [`tHospitals`](#thospitals)): which hospital this isolate was collected from.
- `order_date` (datetime): when this isolate was collected; named because as a backup we use the timestamp for when collection was ordered when an exact collection time is unavailable.
- `collection_unit` (string): the name of the unit within the hospital represented by `hospital_ID` where collection occurred. Can be any string.
- `collection_sourceA` (string): optional. The first of two descriptors for how the specimen was collected.
- `collection_sourceB` (string): optional. The second of two descriptors for how the specimen was collected.
- `procedure_desc` (string): describes what type of procedure was used to collect the specimen, e.g. a blood culture, a urine culture, a wound culture, etc.
- `procedure_code` (string): the code used by the EMR to distinguish different procedures, sometimes useful when `procedure_desc` is ambiguous.

[erap]: https://erap.mssm.edu

### tHospitals

FIXME: Continue table by table documentation.

### tOrganisms

### tPatientEncounter

### tIsolateTests

### tIsolateTestResults
