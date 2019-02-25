require 'mysql2'
require 'sequel'

class PathogenDBClient
  
  def initialize(connection_string=nil, opts={})
    raise ArgumentError, "FATAL: PathogenDBClient requires a connection_string" unless connection_string
    @db = Sequel.connect(connection_string)
    if opts[:adapter]
      STDERR.puts "WARN: Overriding PathogenDBClient methods using adapter '#{opts[:adapter]}'"
      require_relative "./pathogendb_adapter_#{opts[:adapter].downcase}"
      extend Object.const_get("PathogenDBAdapter#{opts[:adapter]}")
    end
  end
  
  def assemblies(where_clause=nil)
    if where_clause.is_a? Array
      where_clause = {assembly_id_field => where_clause}
    end
    dataset = @db[:tAssemblies]
        .left_join(:tExtracts, :extract_ID => :extract_ID)
        .left_join(:tStocks, :stock_ID => :stock_ID)
        .left_join(:tIsolates, :isolate_ID => :isolate_ID)
        .left_join(:tOrganisms, :organism_ID => :organism_ID)
    dataset = dataset.where(where_clause) if where_clause
    dataset
  end
  
  def assembly_id_field
    :assembly_data_link
  end
  
  def assembly_paths(base_path, where_clause=nil)
    names = assemblies(where_clause).select_map(assembly_id_field)
    paths = names.map{ |n| File.expand_path("#{n}/#{n}.fasta", base_path) }
    paths.select do |f|
      File.exist?(f) or STDERR.puts "WARN: Queried assembly #{f} not found; skipping"
    end
  end
  
  def clean_genome_name_regex
    nil
  end
  
  def path_to_genome_name(path)
    genome_name = File.basename(path).sub(/\.\w+$/, '')
    if clean_genome_name_regex
      genome_name = genome_name.gsub(Regexp.new(clean_genome_name_regex), '')
    end
    genome_name
  end
  
  def isolates(where_clause=nil)
    dataset = @db[:tIsolates]
        .left_join(:tOrganisms, :organism_ID => :organism_ID)
    dataset = dataset.where(where_clause) if where_clause
    dataset
  end
  
  def encounters(where_clause=nil)
    erap_ids = assemblies(where_clause).select_map(:eRAP_ID).uniq
    dataset = @db[:tPatientEncounter]
        .select(:eRAP_ID,
                Sequel.as(:start_date, :start_time),
                Sequel.as(:end_date, :end_time),
                :department_name,
                :encounter_type,
                :age,
                :sex,
                :transfer_to)
        .where(:eRAP_ID => erap_ids)
        .exclude(:department_name => '')
    dataset
  end
  
end
