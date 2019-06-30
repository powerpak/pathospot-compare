require 'sequel'
require 'tqdm'
require_relative './pathogendb_client'
require 'pp' #FIXME: remove

class PathogenDBCreator < PathogenDBClient
  
  TABLES_TO_COPY = [
    {
      table: :tAssemblies,
      match_on: nil,
      keep_cols: [:auto_ID, :extract_ID, :assembly_ID, :mlst_subtype, :assembly_data_link,
          :contig_count, :contig_N50, :contig_maxlength, :contig_maxID, :qc_failed, :contig_sumlength]
    },
    {
      table: :tExtracts, 
      match_on: :tExtracts__extract_ID,
      keep_cols: [:extract_ID, :stock_ID]
    },
    {
      table: :tStocks,
      match_on: :tStocks__stock_ID,
      keep_cols: [:stock_ID, :isolate_ID]
    },
    {
      table: :tIsolates,
      match_on: :tIsolates__isolate_ID,
      keep_cols: [:isolate_ID, :eRAP_ID, :organism_ID, :hospital_ID, :order_date, :collection_unit, 
          :collection_sourceA, :collection_sourceB, :procedure_desc, :procedure_code]
    },
    {
      table: :tOrganisms, 
      match_on: :tOrganisms__organism_ID
    },
    {
      table: :tHospitals 
      # Without any match_on:, the whole table will be copied.
    },
    {
      table: :tPatientEncounter,
      match_on: :eRAP_ID,
      keep_cols: [:auto_ID, :eRAP_ID, :start_date, :end_date, :hospital_ID, :department_name, 
          :transfer_to, :encounter_type, :age, :sex]
    },
    {
      table: :tIsolateTests,
      match_on: :eRAP_ID
    },
    {
      table: :tIsolateTestResults,
      match_on: :eRAP_ID,
      # With join_for_match_on:, a left join is performed before attempting to match match_on: with 
      # the assembly data
      join_for_match_on: [:tIsolateTests, :test_ID => :tIsolateTestResults__test_ID]
    }
  ]
  
  COLUMNS_TO_DEIDENTIFY = {
    pt_ids: [:tIsolates__eRAP_ID, :tPatientEncounter__eRAP_ID, :tIsolateTests__eRAP_ID],
    datetimes: [:tIsolates__order_date, :tPatientEncounter__start_date, :tPatientEncounter__end_date],
    dates: [:tIsolateTests__test_date],
    units: [
      [:tIsolates__hospital_ID, :tIsolates__collection_unit], 
      [:tPatientEncounter__hospital_ID, :tPatientEncounter__department_name], 
      [:tPatientEncounter__hospital_ID, :tPatientEncounter__transfer_to]
    ]
  }
  
  INPT_UNITS_COLUMNS = [:tPatientEncounter__hospital_ID, :tPatientEncounter__department_name]
  INPT_SELECTOR = {encounter_type: "Hospital Encounter"}
  
  def copy_tables_for_assemblies!(from_data)
    from_db = get_db(from_data)
    
    TABLES_TO_COPY.each do |spec|
      match_on = spec[:table] == :tAssemblies ? assembly_id_field : spec[:match_on]
      table_data = from_db[spec[:table]]
      if match_on
        if spec[:join_for_match_on]
          columns = table_data.columns.map{ |col| [spec[:table], col].join('__').to_sym }
          table_data = table_data.select(*columns).left_join(*spec[:join_for_match_on])
        end
        table_data = table_data.where(match_on => from_data.select_map(match_on).uniq)
      end
      copy_table_structure!(from_db, spec[:table]) unless @db.tables.include?(spec[:table])
      @db[spec[:table]].multi_insert(table_data.all)
    end
  end
  
  def copy_isolates!(from_data)
    from_db = get_db(from_data)
    isolate_ids = from_data.select_map(:tIsolates__isolate_ID).uniq
    table_data = from_db[:tIsolates].where(isolate_ID: isolate_ids)
    
    if @db.tables.include?(:tIsolates)
      # If the table was already partially copied (as it would be in #copy_tables_for_assemblies),
      # don't recopy data that was already copied
      table_data = table_data.exclude(isolate_ID: @db[:tIsolates].select_map(:isolate_ID).uniq)
    else
      # Otherwise, create the table structure
      copy_table_structure!(from_db, :tIsolates)
    end
    @db[:tIsolates].multi_insert(table_data.all)
  end
  
  def deidentify!(keyfiles_prefix=nil)
    # Use the provided PRNG seed if provided, to allow for consistent Array#shuffle results if desired
    srand @srand unless @srand.nil?
    
    # Drop any columns that are not in the whitelist of columns to keep
    TABLES_TO_COPY.each do |spec|
      next unless spec[:keep_cols] # No whitelist for a table implies keeping all columns
      @db[spec[:table]].columns.each do |col|
        @db.alter_table(spec[:table]) { drop_column(col) } unless spec[:keep_cols].include?(col)
      end
    end
    
    # Recode anonymized patient IDs to the smallest necessary range
    eRAP_IDs = get_all_values(COLUMNS_TO_DEIDENTIFY[:pt_ids]).shuffle
    eRAP_ID_key = Hash[eRAP_IDs.zip(1..eRAP_IDs.size)]
    save_key!(eRAP_ID_key, keyfiles_prefix, "erap_IDs") if keyfiles_prefix
    translate_values!(COLUMNS_TO_DEIDENTIFY[:pt_ids], eRAP_ID_key)
    
    # Ensure tPatientEncounter.age is capped at 90 (which indicates 90 or older)
    @db[:tPatientEncounter].where{age > 90}.update(age: 90)
    
    # Shift datetime columns by pseudorandom number of days, between 3-6 years into the future
    shift_days = rand(365 * 3) + 365 * 3
    shift_datetimes!(COLUMNS_TO_DEIDENTIFY[:datetimes], shift_days)
    shift_dates!(COLUMNS_TO_DEIDENTIFY[:dates], shift_days)
    
    # Deidentify locations. Subcategorize into ED, ICU, non-ICU ward, etc., then 
    # assign opaque letter or number codes.
    units = get_all_values(COLUMNS_TO_DEIDENTIFY[:units]).shuffle
    inpt_units = get_all_values([INPT_UNITS_COLUMNS], INPT_SELECTOR).shuffle
    unit_categories = categorize_units(units, inpt_units)
    unit_key = key_from_unit_categories(unit_categories)
    save_key!(unit_key, keyfiles_prefix, "units") if keyfiles_prefix
    translate_values!(COLUMNS_TO_DEIDENTIFY[:units], unit_key)
    
    # IMPORTANT: Must rebuild the database, otherwise deleted data is left behind in unused pages!
    @db.run "VACUUM" unless @db.adapter_scheme != :sqlite
  end
  
  
  private
  
  def initialize(connection_string=nil, opts={})
    super
    @srand = opts[:srand]
  end
  
  # Get the Sequel::Database object associated with the Sequel::Dataset passed in as a first argument
  # It must not be the same as the @db in use by this instance
  def get_db(dataset)
    raise ArgumentError, "FATAL: requires a `Sequel::Dataset`" unless dataset.is_a? Sequel::Dataset
    raise ArgumentError, "FATAL: can't copy within same db" unless dataset.db.uri != @db.uri
    dataset.db
  end
  
  # Copy the structure (columns, types, primary keys, etc.) of a table in a Sequel::Database to @db
  def copy_table_structure!(from_db, table_name)
    @db.create_table(table_name) do
      from_db.schema(table_name).each do |col|
        column(col[0], col[1][:type], col[1])
      end
    end
  end
  
  # returns the column name that is the primary key for a given table
  def primary_key_col(table_name)
    pk_cols = @db.schema(table_name).select{ |col| col[1][:primary_key] }
    raise ArgumentError, "FATAL: #{table_name} schema has !=1 primary key cols" if pk_cols.size != 1
    pk_cols.first.first
  end
  
  # Given an enumerable of qualified column names, returns the table name common to all of them
  # If there are multiple table names, raise an error
  def table_from_columnset(colset)
    tbls = colset.map{ |col| col.to_s.sub(/__\w+/, '').to_sym}.uniq
    raise ArgumentError, "FATAL: Cannot rekey sets of columns that span multiple tables" if tbls.size > 1
    tbls.first
  end
  
  # For an array of [potentially arrays of] qualified column names, produce an array of all unique values
  # found in those columns. If column names are grouped as arrays of arrays, then all unique tuples of the
  # values found in those columns are returned.
  def get_all_values(columnsets, where=nil)
    vals = []
    columnsets.each do |colset|
      colset = [colset] unless colset.is_a? Enumerable
      tbls = colset.map{ |col| col.to_s.sub(/__\w+/, '').to_sym}.uniq
      raise ArgumentError, "FATAL: Cannot query across multiple tables in #get_all_values" if tbls.size > 1
      dataset = where ? @db[tbls.first].where(where) : @db[tbls.first]
      colset.each{ |col| dataset = dataset.exclude(col => '') }
      vals += dataset.select_map(colset)
    end
    vals.uniq
  end
  
  # Perform some safety checks on a translation key.
  def validate_translation_key(translation_key)
    dup_values = translation_key.values.size != translation_key.values.uniq.size
    raise ArgumentError, "FATAL: translation key contains duplicate output values" if dup_values
  end
  
  # Given an array of [possibly arrays of] qualified column names and a hashmap of old to new values, 
  # translate those columns. If the input is an array of array of column names, the hashmap of old to new
  # values should contain tuples of values (enough for each of the sets of columns).
  def translate_values!(columnsets, translation_key)
    validate_translation_key(translation_key)
    columnsets.each do |colset|
      colset = [colset] unless colset.is_a? Enumerable
      tbl = table_from_columnset(colset)
      cols_unqualified = colset.map{ |col| col.to_s.split('__', 2).map(&:to_sym).last }
      pk_key = {}
      pk_col = primary_key_col(tbl)
      desc = "Rekey #{cols_unqualified.join(", ")} in table #{tbl}"
      translation_key.each do |from, to|
        from = [from] unless from.is_a? Enumerable
        to = [to] unless to.is_a? Enumerable
        pks = @db[tbl].where(Hash[[cols_unqualified, from].transpose]).select_map(pk_col)
        pk_key[pks] = to unless pks.size == 0
      end
      pk_key.tqdm(desc: desc, leave: true).each do |from, to|
        @db[tbl].where(pk_col => from).update(Hash[[cols_unqualified, to].transpose])
      end
    end
  end
  
  # Given an array of qualified column names and a hashmap of old to new values, translate those columns
  # Optionally, set `is_date` to true to manipulate a date column (without times)
  def shift_datetimes!(columns, shift_days, is_date=false)
    columns.each do |col|
      tbl, col_unqualified = col.to_s.split('__').map(&:to_sym)
      # Uses SQLite's datetime() or date() function to recompute a date[time] shifted by a number of days
      # See also: https://www.tutlane.com/tutorial/sqlite/sqlite-datetime-function
      update_fn = Sequel.function(is_date ? :date : :datetime, col_unqualified, "#{shift_days} days")
      @db[tbl].update(col_unqualified => update_fn)
    end
  end
  def shift_dates!(*args)
    shift_datetimes!(*args, true)
  end
  
  # Given an array of units and inpatient units, subcategorize them into a hash, which is returned
  # Note that this is necessarily specific to Mount Sinai's ward naming
  def categorize_units(units, inpt_units)
    unit_categorization = {
      "ED" => [inpt_units, nil, /^EMERGENCY|\bED\b/],
      "PACU" => [units, nil, /PACU|PERIOP|^CCIP$|^[RC]PAC$/],
      "ORs" => [units, nil, /OPERATING ROOM|CATHETERIZATION|ENDOSCOPY/],
      "NICU" => [inpt_units, nil, /^NICU$/],
      "PICU" => [inpt_units, nil, /^PICU$|^PEDS CTICU$/],
      "ICU" => [inpt_units, nil, /^([MSTC]ICU|CCU|CSIU|NSIC)$/],
      "Rads" => [inpt_units, nil, /RADIOLOGY|INTERV RAD/i ],
      "Dialysis" => [units, nil, /DIALYSIS/i ]
    }
    
    unit_categories = {}
    unit_categorization.each do |cat, criteria|
      matched = criteria.shift
      criteria.each_with_index do |criterion, i|
        next unless criterion
        matched = matched.select{ |vals| vals[i] =~ criterion }
      end
      unit_categories[cat] = matched
    end
    
    unit_categories["Ward"] = inpt_units - unit_categories.values.flatten(1)
    unit_categories["Outpt"] = units - unit_categories.values.flatten(1)
    unit_categories
  end
  
  def key_from_unit_categories(unit_categories)
    unit_key = {}
    unit_categories.each do |cat, units|
      units_by_hosp_id = units.group_by{ |unit_tup| unit_tup[0] }
      units_by_hosp_id.each do |hosp_id, units|
        if units.size == 1
          unit_key[units.first] = [hosp_id, cat]
        else
          units.each_with_index{|unit, i| unit_key[unit] = [hosp_id, "#{cat} #{i + 1}"] }
        end
      end
    end
    unit_key
  end
  
  # Given a key of values to be translated (which may be tuples), write all the from/to pairs to
  # a TSV file
  def save_key!(key, keyfiles_prefix, keyfile_name)
    File.open("#{keyfiles_prefix}.#{keyfile_name}.tsv", 'w') do |f|
      key.each do |from, to|
        f.puts([from, to].flatten.join("\t"))
      end
    end
  end
  
end