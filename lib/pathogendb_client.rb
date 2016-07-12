require 'mysql2'
require 'sequel'

class PathogenDBClient
  
  def initialize(connection_string=nil)
    raise ArgumentError, "FATAL: PathogenDBClient requires a connection_string" unless connection_string
    @db = Sequel.connect(connection_string)
  end
  
end
