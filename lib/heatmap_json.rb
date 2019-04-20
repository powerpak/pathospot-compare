require_relative './pathogendb_client'

INTERESTING_COLS = [:assembly_ID, :eRAP_ID, :mlst_subtype, :isolate_ID, :procedure_desc, :order_date, 
      :collection_unit, :contig_count, :contig_N50, :contig_maxlength]
EXPECTED_HEATMAP_JSON_OPTS = [:distance_unit, :in_query, :out_dir]

def heatmap_json(in_paths, mysql_uri, opts)
  pdb = PathogenDBClient.new(mysql_uri, opts)
  
  json = {
    generated: DateTime.now.to_s,
    distance_unit: opts[:distance_unit] || "nucmer SNVs",
    in_query: opts[:in_query],
    out_dir: opts[:out_dir],
    nodes: [[:name] + INTERESTING_COLS],
    links: []
  }
  # Any other keys in opts get merged into the very end of the json object
  json.merge!(opts.reject{ |k, v| EXPECTED_HEATMAP_JSON_OPTS.include?(k) })
  
  genome_names = in_paths && in_paths.map{ |path| pdb.path_to_genome_name(path) }
  assemblies = pdb.assemblies(genome_names)
  node_hash = Hash[genome_names.map{ |n| [n, {}] }]
  assemblies.each do |row|
    node_hash[row[pdb.assembly_id_field].to_s][:metadata] = row
  end

  node_hash.each do |k, v|
    node = [k]
    unless v[:metadata]
      puts "WARN: No PathogenDB metadata found for assembly #{k}; skipping"; next
    end
    INTERESTING_COLS.each do |col|
      meta = v[:metadata][col]
      node << (meta.is_a?(Time) ? meta.strftime("%FT%T%:z") : meta)
    end
    json[:nodes] << node
    v[:id] = json[:nodes].size - 2              # The header row doesn't count!
  end

  json[:links] = Array.new(json[:nodes].size - 1){ Array.new(json[:nodes].size - 1, nil) }
  yield(json, node_hash)
  json
end