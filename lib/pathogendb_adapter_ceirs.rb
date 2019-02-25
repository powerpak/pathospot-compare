module PathogenDBAdapterCEIRS
  
  # Maps columns in the tCEIRS_* tables to their equivalent columns in the 
  # bacterial CML tables. Ultimately, we only care about mapping the fields that
  # are used in the .heatmap.json file, i.e., refer to the INTERESTING_COLS in 
  # heatmap_json.rb.
  def assemblies(where_clause=nil)
    if where_clause.is_a? Array
      where_clause = {assembly_id_field => where_clause}
    end
    dataset = @db[:tCEIRS_assemblies]
        .left_join(:tCEIRS_Extracts, :Extract_ID => :Extract_ID)
        .left_join(:tCEIRS_Isolates, :Isolate_ID => :Isolate_ID)
        .left_join(:tPVI_Surveillance, :specimen_ID => :Sample_Name)
        .left_join(:tIsolates, :isolate_ID => :cml_isolate_id)
        .left_join(:tHospitals, :hospital_ID => :tPVI_Surveillance__hospital_ID)
    dataset = dataset.select(:assembly_ID)
        .select_append(Sequel.as(
            Sequel.function(:IFNULL, :tPVI_Surveillance__eRAP_ID, :Sample_Name),
            :eRAP_ID))
        .select_append(Sequel.as(:assembly_subtype, :mlst_subtype))
        .select_append(Sequel.as(:tCEIRS_Isolates__Isolate_ID, :isolate_ID))
        .select_append(:procedure_desc)
        .select_append(Sequel.as(:tPVI_Surveillance__sample_date, :order_date))
        .select_append(Sequel.as(
            Sequel.function(:IFNULL, :collection_unit, :hospital_abbreviation), 
            :collection_unit))
    dataset = dataset.where(where_clause) if where_clause
    dataset
  end
  
  def assembly_id_field
    :assembly_ID
  end
  
  def assembly_paths(base_path, where_clause=nil)
    names = assemblies(where_clause).select_map(assembly_id_field)
    paths = names.map do |n|
      glob = File.expand_path("#{n}/??_#{n}_final.fa", base_path)
      Dir.glob(glob).first || glob
    end
    paths.select do |f|
      File.exist?(f) or puts "WARN: Queried assembly #{f} not found; skipping"
    end
  end
  
  def clean_genome_name_regex
    '^\w{2}_|_final$'
  end
  
end