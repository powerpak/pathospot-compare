require 'sequel'
require_relative './pathogendb_client'

class PathogenDBCreator < PathogenDBClient
  
  def get_db(dataset)
    raise ArgumentError, "FATAL: requires a `Sequel::Dataset`" unless dataset.is_a? Sequel::Dataset
    raise ArgumentError, "FATAL: can't copy within same db" unless dataset.db.uri != @db.uri
    dataset.db
  end
  
  def copy_table_structure(from_db, table_name)
    @db.create_table(table_name) do
      from_db.schema(table_name).each do |col|
        column(col[0], col[1][:name], col[1])
      end
    end
  end
  
  TABLES_TO_COPY = [
    {table: :tAssemblies, match_on: nil},
    {table: :tExtracts, match_on: :tExtracts__extract_ID},
    {table: :tStocks, match_on: :tStocks__stock_ID},
    {table: :tIsolates, match_on: :tIsolates__isolate_ID},
    {table: :tOrganisms, match_on: :tOrganisms__organism_ID},
    {table: :tPatientEncounter, match_on: :eRAP_ID}
  ]
  
  def copy_tables_for_assemblies(from_data)
    from_db = get_db(from_data)
    
    TABLES_TO_COPY.each do |spec|
      match_on = spec[:match_on] || assembly_id_field
      table_ids = from_data.select_map(match_on).uniq
      table_data = from_db[spec[:table]].where(match_on => table_ids).all
      copy_table_structure(from_db, spec[:table]) unless @db.tables.include?(spec[:table])
      @db[spec[:table]].multi_insert(table_data)
    end
  end
  
  def copy_isolates(from_data)
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
      copy_table_structure(from_db, :tIsolates)
    end
    @db[:tIsolates].multi_insert(table_data.all)
  end
  
end