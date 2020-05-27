# Creating your own metadata database

We store all of the interesting information associated with each input genome in a relational database that **pathospot-compare** incorporates into the analysis. Additional data providing epidemiological context, such as patient movements and microbiology test results for additional specimens, are also stored here. It cannot be underemphasized [how vital these contextual metadata are][natmic] when attempting to interpret outbreak phylogenies.

[natmic]: https://www.nature.com/articles/s41564-020-0738-5

The [example dataset (tar.gz)](https://pathospot.org/data/mrsa.tar.gz) includes `mrsa.db`, which is an [SQLite] database. SQLite is a free and widely used database format, with many open source GUI tools available (see below). The easiest way to create an metadata database for your own specimens is to open our example and modify the data inside, retaining the same table and column structure.

[SQLite]: https://www.sqlite.org/index.html

Below, we answer the most [frequently asked questions](#faq), and then provide some formal documentation on the [database schema](#schema).

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

You do not; you can use any database that [Sequel](https://sequel.jeremyevans.net/), our Ruby database library, has adapters for. If you like MySQL, for instance, you may create a database, edit it with [phpMyAdmin](https://www.phpmyadmin.net/), and then connect to it with a `PATHOGENDB_URI` of the form `mysql2://user:password@host/db_name`. 

## Schema

An abbreviated graphical summary of the schema follows (click to see the full version with all fields included).

<a href="https://pathospot.org/images/schema-large.png"><img src="https://pathospot.org/images/schema-compact.png" /></a>

In this schema, the major landmarks are:

- [`tAssemblies`](#tassemblies), which contains metadata on the _sequenced_ isolates and corresponds 1:1 with the FASTA/BED files in `IGB_DIR`--they are linked by `assembly_data_link` which contains the name of the FASTA file and its parent directory.
- [`tIsolates`](#tisolates), which contains metadata on both _sequenced_ and _collected but not sequenced_ isolates, and links them to patients via `eRAP_ID` and locations via `hospital_ID` and `collection_unit`.
- [`tPatientEncounter`](#tpatientencounter), which contains data on patient movements through the hospitals
- [`tIsolateTests`](#tisolatetests), which contains data on microbiology tests for the patients (that may or may not yield isolates, as in [`tIsolates`](#tisolates)).

You may notice that we chain through two intermediary tables, [`tStocks`](#tstocks) and [`tExtracts`](#textracts), to get from [`tAssemblies`](#tassemblies) to their respective [`tIsolates`](#tisolates). This is because we prefer to store the provenance of intermediary steps in our stocking and sequencing process in case they need to be debugged or repeated. If you don't need such detail, you can feel free to use the exact same string for `isolate_ID`, `stock_ID`, `extract_ID`, and `assembly_ID`, and simply create dummy entries in [`tStocks`](#tstocks) and [`tExtracts`](#textracts) for each assembly-isolate pair to link them all together.

You may add columns to any of the tables to store additional fields, or additional tables; the following represents a minimal schema rather than an exact requirement. In the following descriptions, **PK** refers to a _primary key_, and **FK** refers to a _foreign key_.

### tAssemblies

Rows of this table associate metadata with each of the FASTA _sequences_ that you store in `IGB_DIR`. We call these sequences _assemblies_ because we attempt to assemble complete genomes for all isolates from PacBio long reads, but technically, your sequences can be genome fragments assembled from short reads, [core genomes](http://www.metagenomics.wiki/pdf/definition/pangenome), or smaller sets of housekeeping genes as in [MLST][]. Note that less complete sequences will lead to less optimal alignments and decrease your confidence in distinguishing closely related strains.

[MLST]: http://pubmlst.org/

This table should include the following fields:

- `auto_ID` (integer; **PK**): An autoincrementing integer ID for this table.
- `extract_ID` (string; **FK** to [`tExtracts`](#textracts)): the extract that was sequenced to create this assembly.
- `assembly_ID` (string): a string that uniquely identifies this assembly. Can contain `A-Za-z0-9._-`; we choose to use numeric strings.
- `mlst_subtype` (string): optional. The [MLST][] sequence type for this assembly, if you have it.
- `assembly_data_link` (string): The name of the FASTA file for this sequence (minus the extension), which is also the name of its parent directory within `IGB_DIR`. Like `assembly_ID`, this should also be unique.
- `contig_count` (integer): How many contigs are in your assembly, i.e. the number of separate sequences in the FASTA file.
- `contig_N50` (integer): The minimum contig length needed to [cover 50% of the genome](http://www.metagenomics.wiki/pdf/definition/assembly/n50), when they are ordered from longest to shortest, i.e. a length weighted median.
- `contig_maxlength` (integer): The length of the longest contig.
- `contig_maxID` (string): The ID of the longest contig. In a FASTA file, this is the identifier on the line starting with `>` or `;` preceding the lines of sequence data for that contig.
- `qc_failed` (integer): optional. We set this to a non-zero number if our automatic QC fails on an assembly, so it can be excluded from comparative analysis until it is fixed. Otherwise, set it to **0**.
- `contig_sumlength` (integer): The sum of the lengths of all contigs.

### tExtracts

Before sequencing, we have to extract DNA from a stock, e.g. by pelleting cells and using a [DNA extraction kit](https://www.qiagen.com/lu/products/top-sellers/dneasy-blood-and-tissue-kit/). These extracts are recorded separately in this table, as it may need to be performed multiple times for a stock, e.g., if we need to resequence the same stock multiple times.

This table should include the following fields:

- `extract_ID` (string, **PK**): a unique string that identifies this extract. Can contain `A-Za-z0-9._-`.
- `stock_ID` (string, **FK** to [`tStocks`](#tstocks)): which stock this extract was created from.

### tStocks

For all isolates produced by our [clinical microbiology lab][cml] that we bank for sequencing, we create one or more frozen stocks. This table tracks the stocks and links them to the isolates they were created from.

This table should include the following fields:

- `stock_ID` (string, **PK**): a unique string that identifies this stock. Can contain `A-Za-z0-9._-`.
- `isolate_ID` (string, **FK** to [`tIsolates`](#tisolates)): which isolate this stock was created from.

[cml]: https://icahn.mssm.edu/about/departments/pathology/clinical/microbiology/clinical-services

### tIsolates

This table stores metadata on all isolates produced by our [clinical microbiology lab][cml] that are included in active surveillance programs. At a minimum, you need to provide metadata for isolates that are sequenced and have a corresponding entry in [`tAssemblies`](#tassemblies); however you may also provide metadata on isolates that have been recorded and/or banked but not chosen for sequencing, which will be layered on top of the visualizations.

Typically, isolates are collected from positive clinical microbiology tests (such as blood or urine cultures, aka [`tIsolateTests`](#tisolatetest)) and therefore isolates can (optionally) be associated with entries in [`tIsolateTestResults`](#tisolatetestresults).

This table should include the following fields:

- `isolate_ID` (string, **PK**): a unique string that identifies this isolate. Can contain `A-Za-z0-9_-`.
- `eRAP_ID` (integer): an opaque integer ID for the patient that the isolate was collected from. Every patient should have a unique ID. There is no table enumerating patients and patient-specific data in our schema, as these IDs refer directly to entries in a [clinical data warehouse][erap].
- `organism_ID` (integer; **FK** to [`tOrganisms`](#torganisms)): the species that was identified for this isolate.
- `hospital_ID` (integer; **FK** to [`tHospitals`](#thospitals)): which hospital this isolate was collected from.
- `order_date` (datetime): when this isolate was collected; named because as a backup we use the timestamp for when collection was ordered when an exact collection time is unavailable.
- `collection_unit` (string): the name of the unit within the hospital [system] represented by `hospital_ID` where collection occurred. Can be any string.
- `collection_sourceA` (string): optional. The first of two descriptors for how the specimen was collected, e.g. "Venipuncture".
- `collection_sourceB` (string): optional. The second of two descriptors for how the specimen was collected, e.g. "Blood".
- `procedure_desc` (string): describes what type of procedure was used to collect the specimen, e.g. a blood culture, a urine culture, a wound culture, etc. Although we use codes directly from our EMR, e.g. "Culture-blood", you may use more human-friendly names.
- `procedure_code` (string): optional. The code used by the EMR to distinguish different procedures, sometimes useful when `procedure_desc` is ambiguous. We simply store codes from our EMR that have no external meaning.

[erap]: https://erap.mssm.edu

### tHospitals

Stores details on the hospitals included in your database. We tend to use this to refer to hospital _systems_, e.g., including various Mount Sinai affiliated outpatient clinics underneath the umbrella of each parent hospital. If this is not significant in your dataset, you can simply associate all locations with the same `hospital_ID`.

This table should include the following fields:

- `hospital_ID` (integer, **PK**): Unique integer ID for each hospital.
- `hospital_abbreviation` (string): 2 or 3 letter code for the hospital, combined with the unit name to label locations in the visualizations. Multiple hospitals can share the same abbreviation, _however_ all potential combinations of `hospital_abbreviation` with `tIsolateTests.collection_unit`, `tIsolates.collection_unit`, and `tPatientEncounter.department_name` in your data _must_ be unique.
- `hospital_name` (string): optional. The full name of the hospital.
- `hospital_city` (string): optional. City in which the hospital is located, e.g., "New York". 
- `hospital_country` (string): optional. Country in which the hospital is located, e.g., "United States".

### tOrganisms

Details of all the different organisms (i.e. species or subspecies) that are included in your dataset. Our sample dataset includes many common organisms that are revealed by routine clinical microbiological testing; you may continue to use it as is, pare it down to only the organisms you study, expand it as needed, or rebuild it entirely. 

This table should include the following fields:

- `organism_ID` (integer, **PK**): Unique integer ID for each organism.
- `full_name`	(string): optional. The full genus + species name, e.g. "Staphylococcus aureus". May also contain subspecies and other qualifiers, e.g. "Methicillin-resistant".
- `abbreviated_name` (string): optional. An abbreviated name for this species that can be used within filenames and URLs, e.g. "S_aureus". Can contain `A-Za-z0-9_-`.
- `wiki_link` (string): optional. The name of the corresponding Wikipedia page on this organism, e.g. the part of the URL after `https://en.wikipedia.org/wiki/`...
- `taxonomy_ID` (integer): optional. The corresponding NCBI taxonomy ID for this species, e.g., the part of the URL after `https://www.ncbi.nlm.nih.gov/taxonomy/`...
- `gram` (string): optional. Gram staining pattern for this organism, e.g. "Positive or "Negative". Can be left blank for organisms that do not fall into either of those categories.
- `tax_superkingdom` (string): optional. The superkingdom for this species, in biological [taxonomic rank][tr], e.g. "Bacteria".
- `tax_phylum` (string): optional. The phylum for this species, in biological [taxonomic rank][tr], e.g. "Firmicutes".
- `tax_class` (string): optional. The class for this species, in biological [taxonomic rank][tr], e.g. "Bacilli".
- `tax_order` (string): optional. The order for this species, in biological [taxonomic rank][tr], e.g. "Lactobacillales".
- `tax_family` (string): optional. The family for this species, in biological [taxonomic rank][tr], e.g. "Enterococcaceae".
- `tax_genus` (string): optional. The genus for this species, in biological [taxonomic rank][tr], e.g. "Enterococcus".

[tr]: https://en.wikipedia.org/wiki/Taxonomic_rank

### tPatientEncounter

This table contains a row for each _encounter_ between a patient and a particular hospital, usually generated from some combination of [admit-discharge-transfer][adt] (ADT) and other electronic medical record (EMR) data. An encounter is a rather [generic concept][enc] in EMRs for "an interaction between a patient and healthcare provider(s) for the purpose of providing healthcare service(s) or assessing the health status of a patient," but maps roughly to office visits (for outpatient encounters) and a continuous stay in at least one unit at a medical facility (for inpatient encounters). In our schema, we furthermore break down inpatient encounters into separate entries for each unit that the patient passes through (e.g., ED, inpatient ward, ICU), with each transfer event denoted by a `transfer_to` value on the preceding entry to "link" it to the next one.

[adt]: https://en.wikipedia.org/wiki/Admission,_discharge,_and_transfer_system
[enc]: https://www.hl7.org/fhir/encounter-definitions.html

This data is primarily used to build the [dendro-timeline](https://github.com/powerpak/pathospot-visualize#dendro-timelinephp) visualization. _Note that this table is entirely optional, and if it contains no rows, then the timelines will simply appear blank._

This table should include the following fields:

- `auto_ID` (integer, **PK**): An autoincrementing integer ID for this table.
- `eRAP_ID` (integer): An opaque integer ID for the patient that the isolate was collected from. Every patient should have a unique ID. There is no table enumerating patients and patient-specific data in our schema, as these IDs refer directly to entries in a [clinical data warehouse][erap].
- `start_date` (datetime): Timestamp for when the encounter began.
- `end_date` (datetime): Timestamp for when the encounter ended.	
- `hospital_ID` (integer, **FK** to [`tHospitals`](#thospitals)): which hospital or hospital system this encounter occurred within.
- `department_name` (string): optional. The name of the unit, department, or clinic in which this encounter occurred, e.g. "MICU". Although optional, if you don't include a value here, the encounter won't show up in any of the visualizations.
- `transfer_to` (string): optional. If during an inpatient stay this patient transferred to another unit at `end_date`, the `department_name` of the destination should be included here. Leave as the empty string or NULL if this encounter did not end with a transfer to another unit.	
- `encounter_type` (string): Free-form text that describes what kind of encounter occurred; the special value "Hospital Encounter" should be used for all inpatient encounters. For outpatient encounters, values like "Office Visit", "Elective Surgery", "Dialysis" and so on could be used.
- `age` (integer): optional. The age of the patient during this particular encounter, in years. If you choose not to provide this, use the value **-1**.  It is not currently displayed in any of the visualizations.
- `sex` (string): optional. The sex recorded for the patient for this particular encounter, which is either "Male", "Female", or any other value. You may choose to use this for either sex at birth or gender identity. It is not currently displayed in any of the visualizations.

### tIsolateTests

During their various encounters, patients may receive microbiological tests that provide insight on when a patient was first infected or how long it took them to clear a particular infection. Although not all positive cultures will merit sequencing, these other tests (including negative results) can provide helpful clinical context for patients involved in an outbreak, and therefore we support layering these data onto the [dendro-timeline][dt] visualization.

_Note that this table is entirely optional, and if it contains no rows, then the visualizations will continue to function appropriately without the extra data._

[dt]: https://github.com/powerpak/pathospot-visualize#dendro-timelinephp

Each row of this table represents one microbiological test performed on a patient identified by their `eRAP_ID`. As a single test may have zero, one, or multiple results (e.g. zero when it has not yet resulted, and multiple if the result is updated or if multiple isolates are found in one test), we store the results separately, in [`tIsolateTestResults`](#tisolatetestresults). Often this data will be extractable from the EMR or directly from the clinical microbiology laboratory information management system (LIMS).

This table should include the following fields:

- `test_ID` (integer, **PK**): A unique ID for each test performed.
- `eRAP_ID` (integer): An opaque integer ID for the patient that the isolate was collected from. Every patient should have a unique ID. There is no table enumerating patients and patient-specific data in our schema, as these IDs refer directly to entries in a [clinical data warehouse][erap].
- `test_date` (datetime): A timestamp for when the test was performed (we use the collection timestamp for the specimen, or when this is not available, the order timestamp).	
- `hospital_ID` (integer, **FK** to [`tHospitals`](#thospitals)): which hospital or hospital system this encounter occurred within.
- `procedure_name` (string): describes what type of procedure was used to collect the specimen, e.g. a blood culture, a urine culture, a wound culture, etc.; analogous to `tIsolates.procedure_desc`. Although we use codes directly from our EMR, e.g. "CULTURE-BLOOD", you may use more human-friendly names.
- `collection_unit` (string): the name of the unit within the hospital [system] represented by `hospital_ID` where collection occurred. Can be any string. analogous to `tIsolates.collection_unit`.

### tIsolateTestResults

Each row of this table represents a result for a microbiological test recorded in [`tIsolateTests`](#tisolatetests). Tests can have zero, one, or multiple results (e.g. zero when it has not yet resulted, and multiple if the result is updated or if multiple isolates are found in one test). 

_Note that this table is entirely optional, and if it contains no rows, then the visualizations will continue to function appropriately without the extra data._

This table should include the following fields:

- `result_ID` (integer, **PK**): A unique ID for each test result recorded in this table.
- `test_ID` (integer, **FK** to [`tIsolateTestResults`](#thospitals)): which microbiological test this result is associated with. Tests can have zero, one, or multiple results.
- `test_result` (string): A summary of the test outcome. Valid values include the exact strings "positive" and "negative"; any result that is not "negative" is treated equivalently to "positive" for the purposes of drawing the visualizations.
- `description` (string): optional. Additional text explaining the test outcome can be included here, such as "No growth for 5 days."
- `organism_ID` (integer, **FK** to [`tOrganisms`](#torganisms)): optional. If the test result refers to a specific organism, this can be annotated in this field. If not, set to **NULL** or the empty string.
- `isolate_ID` (string, **FK** to [`tIsolates`](#tisolates)): optional. If this test result produced an isolate that was banked and recorded in [`tIsolates`](#tisolates), store a link to it in this field. If not, set to **NULL** or the empty string.
