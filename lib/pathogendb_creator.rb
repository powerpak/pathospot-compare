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
      table: :tPatientEncounter,
      match_on: :eRAP_ID,
      keep_cols: [:auto_ID, :eRAP_ID, :start_date, :end_date, :department_name, :transfer_to, 
          :encounter_type, :age, :sex]
    }
  ]
  
  COLUMNS_TO_DEIDENTIFY = {
    pt_ids: [:tIsolates__eRAP_ID, :tPatientEncounter__eRAP_ID],
    dates: [:tIsolates__order_date, :tPatientEncounter__start_date, :tPatientEncounter__end_date],
    units: [:tPatientEncounter__department_name, :tPatientEncounter__transfer_to, 
        :tIsolates__collection_unit]
  }
  
  INPT_SELECTOR = {encounter_type: "Hospital Encounter"}
  
  def copy_tables_for_assemblies!(from_data)
    from_db = get_db(from_data)
    
    TABLES_TO_COPY.each do |spec|
      match_on = spec[:match_on] || assembly_id_field
      table_ids = from_data.select_map(match_on).uniq
      table_data = from_db[spec[:table]].where(match_on => table_ids).all
      copy_table_structure!(from_db, spec[:table]) unless @db.tables.include?(spec[:table])
      @db[spec[:table]].multi_insert(table_data)
    end
  end
  
  def copy_isolates!(from_data)
    from_db = get_db(from_data)
    
    # The following two lines add dummy data so that columns in `IN_QUERY` specific to `tAssemblies`,
    # e.g., `qc_failed`, have no effect on a query of only `tIsolates`
    dummy_table = @db[:tIsolates].select(:isolate_ID, Sequel.lit('0 as qc_failed'))
    from_data = from_data.join(dummy_table, isolate_ID: :tIsolates__isolate_ID)
    
    isolate_ids = from_data.select_map(:tIsolates__isolate_ID).uniq
    table_data = from_db[@db[:tIsolates]].where(isolate_ID: isolate_ids)
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
  
  def deidentify!()
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
    translate_values!(COLUMNS_TO_DEIDENTIFY[:pt_ids], eRAP_ID_key)
    
    # Ensure tPatientEncounter.age is capped at 90 (which indicates 90 or older)
    @db[:tPatientEncounter].where{age > 90}.update(age: 90)
    
    # Shift datetime columns by pseudorandom number of days, between 3-6 years into the future
    shift_days = rand(365 * 3) + 365 * 3
    shift_datetimes!(COLUMNS_TO_DEIDENTIFY[:dates], shift_days)
    
    # Deidentify locations. Subcategorize into ED, ICU, non-ICU ward, PACU, MSQ, and outpatient, then 
    # assign opaque letter or number codes.
    units = get_all_values(COLUMNS_TO_DEIDENTIFY[:units]).shuffle
    inpt_units = get_all_values([COLUMNS_TO_DEIDENTIFY[:units].first], INPT_SELECTOR).shuffle
    unit_categories = categorize_units(units, inpt_units)
    pp unit_categories #FIXME: remove
    unit_key = key_from_unit_categories(unit_categories)
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
  
  # For an array of qualified column names, produce an array of all unique values in those columns
  def get_all_values(columns, where=nil)
    vals = []
    columns.each do |col|
      tbl = col.to_s.sub(/__\w+/, '').to_sym
      dataset = where ? @db[tbl].where(where) : @db[tbl]
      vals += dataset.exclude(col => '').select_map(col)
    end
    vals.uniq
  end
  
  # Perform some safety checks on a translation key.
  def validate_translation_key(translation_key)
    dup_values = translation_key.values.size != translation_key.values.uniq.size
    raise ArgumentError, "FATAL: translation key contains duplicate output values" if dup_values
  end
  
  # Given an array of qualified column names and a hashmap of old to new values, translate those columns 
  def translate_values!(columns, translation_key)
    validate_translation_key(translation_key)
    columns.each do |col|
      tbl, col_unqualified = col.to_s.split('__').map(&:to_sym)
      pk_key = {}
      pk_col = primary_key_col(tbl)
      desc = "Rekey #{col_unqualified} in table #{tbl}"
      translation_key.each do |from, to|
        pks = @db[tbl].where(col => from).select_map(pk_col)
        pk_key[pks] = to unless pks.size == 0
      end
      pk_key.tqdm(desc: desc, leave: true).each do |from, to|
        @db[tbl].where(pk_col => from).update(col_unqualified => to)
      end
    end
  end
  
  # Given an array of qualified column names and a hashmap of old to new values, translate those columns 
  def shift_datetimes!(columns, shift_days)
    columns.each do |col|
      tbl, col_unqualified = col.to_s.split('__').map(&:to_sym)
      # Uses SQLite's datetime() function to recompute a datetime shifted by a number of days
      # See also: https://www.tutlane.com/tutorial/sqlite/sqlite-datetime-function
      update_fn = Sequel.function(:datetime, col_unqualified, "#{shift_days} days")
      @db[tbl].update(col_unqualified => update_fn)
    end
  end
  
  # Given an array of units and inpatient units, subcategorize them into a hash, which is returned
  # Note that this is necessarily specific to Mount Sinai's ward naming
  def categorize_units(units, inpt_units)
    unit_categories = {
      "ED Main" => ["EMERGENCY DEPARTMENT"],
      "ED" => inpt_units.select{ |unit| unit =~ /^EMERGENCY|\bED\b/ } - ["EMERGENCY DEPARTMENT"],
      "PACU" => units.select{ |unit| unit =~ /PACU|PERIOP|^CCIP$|^[RC]PAC$/ },
      "ORs" => units.select{ |unit| unit =~ /OPERATING ROOM|CATHETERIZATION|ENDOSCOPY/ },
      "NICU" => ["NICU"],
      "PICU" => ["PICU", "PEDS CTICU"].shuffle,
      "MSQ ICU" => inpt_units.select{ |unit| unit =~ /^MSQ.*ICU$/ },
      "MSQ" => inpt_units.select{ |unit| unit =~ /^MSQ .*(EAST|WEST|AMB SURG)/ },
      "MSW" => inpt_units.select{ |unit| unit =~ /^MAIN .*/ },
      "MSSL" => inpt_units.select{ |unit| unit =~ /^(BABCOCK|CLARK) / },
      "ICU" => inpt_units.select{ |unit| unit =~ /^([MSTC]ICU|CCU|CSIU|NSIC)$/},
      "Rads" => units.select{ |unit| unit =~ /RADIOLOGY|INTERV RAD/i },
      "Dialysis" => units.select{ |unit| unit =~ /DIALYSIS/i }
    }
    unit_categories["Ward"] = inpt_units - unit_categories.values.flatten
    unit_categories["Outpt"] = units - unit_categories.values.flatten
    unit_categories
  end
  
  def key_from_unit_categories(unit_categories)
    unit_key = {}
    unit_categories.each do |cat, units|
      if units.size == 1
        unit_key[units.first] = cat
      else
        units.each_with_index{|unit, i| unit_key[unit] = "#{cat} #{i + 1}" }
      end
    end
    unit_key
  end
  
end