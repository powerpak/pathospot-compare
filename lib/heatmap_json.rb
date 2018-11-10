require_relative './pathogendb_client'

INTERESTING_COLS = [:eRAP_ID, :mlst_subtype, :assembly_ID, :isolate_ID, :procedure_desc, :order_date, 
      :collection_unit, :contig_count, :contig_N50, :contig_maxlength]

def heatmap_json(in_paths, mysql_uri, opts)
  pdb = PathogenDBClient.new(mysql_uri)
  
  json = {
    generated: DateTime.now.to_s,
    distance_unit: opts[:distance_unit] || "nucmer SNVs",
    in_query: opts[:in_query],
    out_dir: opts[:out_dir],
    links: []
  }
  genome_names = in_paths && in_paths.map{ |path| File.basename(path).sub(/\.\w+$/, '') }
  assemblies = pdb.assemblies(:assembly_data_link => genome_names)
  node_hash = Hash[genome_names.map{ |n| [n, {}] }]
  assemblies.each do |row|
    node_hash[row[:assembly_data_link]][:metadata] = row
  end

  json[:nodes] = [[:name] + INTERESTING_COLS]   # Add a header row with fieldnames
  node_hash.each do |k, v|
    node = [k]
    unless v[:metadata]
      puts "WARN: No PathogenDB metadata found for assembly #{k}; skipping"; next
    end
    INTERESTING_COLS.each { |col| node << v[:metadata][col] }
    json[:nodes] << node
    v[:id] = json[:nodes].size - 2              # The header row doesn't count!
  end

  json[:links] = Array.new(json[:nodes].size - 1){ Array.new(json[:nodes].size - 1, nil) }
  yield(json, node_hash)
  json
end