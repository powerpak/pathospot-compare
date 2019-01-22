require 'mysql2'
require 'sequel'

class PathogenDBClient
  
  def initialize(connection_string=nil)
    raise ArgumentError, "FATAL: PathogenDBClient requires a connection_string" unless connection_string
    @db = Sequel.connect(connection_string)
  end
  
  def assemblies(where_clause=nil)
    dataset = @db[:tAssemblies]
        .left_join(:tExtracts, :extract_ID => :extract_ID)
        .left_join(:tStocks, :stock_ID => :stock_ID)
        .left_join(:tIsolates, :isolate_ID => :isolate_ID)
        .left_join(:tOrganisms, :organism_ID => :organism_ID)
    dataset = dataset.where(where_clause) if where_clause
    dataset
  end
  
  def assembly_paths(base_path, where_clause=nil)
    names = assemblies(where_clause).select_map(:assembly_data_link)
    paths = names.map{ |n| File.expand_path("#{n}/#{n}.fasta", base_path) }
    paths.select do |f|
      File.exist?(f) or puts "WARN: Queried assembly #{f} not found; skipping"
    end
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
