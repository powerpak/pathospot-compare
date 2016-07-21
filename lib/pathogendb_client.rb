require 'mysql2'
require 'sequel'

class PathogenDBClient
  
  def initialize(connection_string=nil)
    raise ArgumentError, "FATAL: PathogenDBClient requires a connection_string" unless connection_string
    @db = Sequel.connect(connection_string)
  end
  
  def assemblies(where_sql=nil)
    dataset = @db[:tAssemblies]
        .left_join(:tExtracts, :extract_ID => :extract_ID)
        .left_join(:tStocks, :stock_ID => :stock_ID)
        .left_join(:tIsolates, :isolate_ID => :isolate_ID)
        .left_join(:tOrganisms, :organism_ID => :organism_ID)
    dataset = dataset.where(where_sql) if where_sql
    dataset
  end
  
  def assembly_paths(base_path, where_sql=nil)
    names = assemblies(where_sql).select_map(:assembly_data_link)
    names.map{ |n| File.expand_path("#{n}/#{n}.fasta", base_path) }
  end
  
end
