require 'mysql2'
require 'sqlite3'
require 'sequel'

class PathogenDBClient
  
  # What columns in tAssemblies should be faked as dummy columns in tIsolates?
  # This allows the same `where_clause` to be applied to both `#assemblies` and `#isolates`
  #    (convenient for running multiple tasks in the Rakefile, e.g. parsnp and epi, with the same parameters)
  # This is a hash of column names => dummy values
  ISOLATE_DUMMY_COLUMNS = {
    qc_failed: 0
  }
  
  def initialize(connection_string=nil, opts={})
    raise ArgumentError, "FATAL: PathogenDBClient requires a connection_string" unless connection_string
    @db = Sequel.connect(connection_string)
    
    # Although this looks like a no-op, it ensures the database connection has actually been opened
    # Otherwise Sequel will lazily connect, and with SQLite, it won't work if Dir.pwd has changed
    @tables = @db.tables
    
    if opts[:adapter]
      STDERR.puts "WARN: Overriding PathogenDBClient methods using adapter '#{opts[:adapter]}'"
      require_relative "./pathogendb_adapter_#{opts[:adapter].downcase}"
      extend Object.const_get("PathogenDBAdapter#{opts[:adapter]}")
    end
  end
    
  # Select assemblies from the database, prejoined with all dependent tables, based on a SQL `where_clause`
  # `where_clause` can be an `Array`, in which case it is a list of assembly names
  def assemblies(where_clause=nil)
    if where_clause.is_a? Array
      where_clause = {assembly_id_field => where_clause}
    end
    dataset = @db[:tAssemblies]
        .left_join(:tExtracts, :extract_ID => :extract_ID)
        .left_join(:tStocks, :stock_ID => :stock_ID)
        .left_join(:tIsolates, :isolate_ID => :isolate_ID)
        .left_join(:tOrganisms, :organism_ID => :organism_ID)
        .left_join(:tHospitals, :hospital_ID => :tIsolates__hospital_ID)
    dataset = dataset.where(where_clause) if where_clause
    dataset
  end
  
  def assembly_id_field(fully_qualified=false); :assembly_data_link; end
  
  def assembly_paths(base_path, where_clause=nil)
    names = assemblies(where_clause).select_map(assembly_id_field)
    paths = names.map{ |n| File.expand_path("#{n}/#{n}.fasta", base_path) }
    paths.select do |f|
      File.exist?(f) or STDERR.puts "WARN: Queried assembly #{f} not found; skipping"
    end
  end
  
  def clean_genome_name_regex; nil; end
  
  def path_to_genome_name(path)
    genome_name = File.basename(path).sub(/(\.\w+)+$/, '')
    if clean_genome_name_regex
      genome_name = genome_name.gsub(Regexp.new(clean_genome_name_regex), '')
    end
    genome_name
  end
  
  def genome_annotation_format; ".bed"; end
  
  # Which NCBI genetic code is used by the pathogens in this database. Necessary for
  # correct variant annotation. Default is 11 for bacteria.
  # See https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi for all choices.
  def genetic_code_table; 11; end
  
  # Adds dummy columns to queries of `tIsolates` so that columns in `IN_QUERY` specific to `tAssemblies`,
  # e.g., `qc_failed`, have no effect on a query of only `tIsolates`
  def add_isolates_dummy_columns(dataset, extra_cols=ISOLATE_DUMMY_COLUMNS)
    dummy_cols = [:isolate_ID]
    extra_cols.each do |name, val|
      dummy_cols << Sequel.lit("#{@db.literal(val)} as #{@db.literal(name)}")
    end
    dummy_table = @db[:tIsolates].select(*dummy_cols)
    dataset.join(dummy_table, isolate_ID: :tIsolates__isolate_ID)
  end
  
  # Select isolates from the database, prejoined with all dependent tables, based an a SQL `where_clause`
  # By default dummy columns are added so that if the `where_clause` mentions columns in tAssemblies
  # (see `ISOLATE_DUMMY_COLUMNS` above), the query still succeeds; to turn this off, set `no_dummy_cols`
  # to `true`
  def isolates(where_clause=nil, no_dummy_cols=false)
    dataset = @db[:tIsolates]
        .left_join(:tOrganisms, :organism_ID => :organism_ID)
        .left_join(:tHospitals, :hospital_ID => :tIsolates__hospital_ID)
    dataset = add_isolates_dummy_columns(dataset) unless no_dummy_cols
    dataset = dataset.where(where_clause) if where_clause
    dataset
  end
  
  def pt_id_field(fully_qualified=false); :eRAP_ID; end
  
  # The where_clause here applies to tAssemblies, and encounters are chosen by eRAP_ID
  def encounters(where_clause=nil)
    erap_ids = assemblies(where_clause).select_map(pt_id_field(true)).uniq
    dataset = @db[:tPatientEncounter]
        .left_join(:tHospitals, :hospital_ID => :tPatientEncounter__hospital_ID)
        .select(:eRAP_ID,
                Sequel.as(:start_date, :start_time),
                Sequel.as(:end_date, :end_time),
                :hospital_abbreviation,
                :department_name,
                :encounter_type,
                :age,
                :sex,
                :transfer_to)
        .where(:eRAP_ID => erap_ids)
        .exclude(:department_name => '')
    dataset
  end
  
  # The where_clause here applies to tAssemblies, and isolate tests are chosen by eRAP_ID
  def isolate_test_results(where_clause=nil)
    erap_ids = assemblies(where_clause).select_map(pt_id_field(true)).uniq
    dataset = @db[:tIsolateTestResults]
        .left_join(:tIsolateTests, :test_ID => :tIsolateTestResults__test_ID)
        .left_join(:tOrganisms, :organism_ID => :tIsolateTestResults__organism_ID)
        .left_join(:tHospitals, :hospital_ID => :tIsolateTests__hospital_ID)
        .select(:tIsolateTestResults__test_ID,
                :eRAP_ID,
                :test_date,
                :hospital_abbreviation,
                :collection_unit,
                :procedure_name,
                :test_result,
                :description,
                :taxonomy_ID,
                :isolate_ID)
        .where(:eRAP_ID => erap_ids)
    dataset
  end
  
  # Helper method for converting timestamps returned within Sequel datasets to ISO 8601
  def stringify_times(enumerable)
    enumerable.map{ |v| v.is_a?(Time) ? v.strftime("%FT%T%:z") : v.to_s }
  end
  
  
end
