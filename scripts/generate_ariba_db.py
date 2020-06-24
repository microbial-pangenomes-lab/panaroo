import os
import tempfile
import argparse

import networkx as nx
from tqdm import tqdm
from collections import defaultdict, Counter
import itertools


def generate_db(gene_data_file, graph_file, outdir, min_support, quiet=False):

    G = nx.read_gml(graph_file)

    # iterate through genes and group centroids that appear together
    tempG = nx.Graph()
    centroids_to_genes = defaultdict(set)
    centroids_to_description = defaultdict(set)
    for n in G.nodes():
        if int(G.nodes[n]['size']) < min_support: continue
        centroids = G.nodes[n]['centroid'].split(";")
        if len(centroids) <= 1:
            tempG.add_node(centroids[0])
        else:
            for nA, nB in itertools.combinations(centroids, 2):
                tempG.add_edge(nA, nB)
        for sid in centroids:
            centroids_to_genes[sid].add(G.nodes[n]['name'])
            for d in G.nodes[n]['description'].split(';'):
                centroids_to_description[sid].add(d)
    clusters = [list(comp) for comp in nx.connected_components(tempG)]

    # name clustes based on genes
    centroids_to_gene_name = {}
    for cluster in clusters:
        name = set()
        for sid in cluster:
            name |= centroids_to_genes[sid]
        name = "~~~".join(list(name))
        for sid in cluster:
            centroids_to_gene_name[sid] = name

    # run through gene_data and pull out the sequences
    with open(outdir+ 'ariba_db.fa', 'w') as ariba_fasta, \
        open(outdir + 'ariba_meta.tsv', 'w') as ariba_meta, \
        open(gene_data_file, 'r') as infile:
        for line in infile:
            line = line.strip().split(',')
            if line[2] in centroids_to_gene_name:
                seqname = line[3] + ';' + line[2]
                ariba_fasta.write('>' + seqname + '\n')
                ariba_fasta.write(line[5] + '\n')

                ariba_meta.write('\t'.join([seqname, '1', '0', '.', 
                    centroids_to_gene_name[line[2]], 
                    ';'.join(centroids_to_description[line[2]])]) + '\n')
    return


def get_options():
    import argparse

    description = 'Create an Ariba database from a Panaroo pangenome'
    parser = argparse.ArgumentParser(description=description,
                                     prog='generate_ariba_db')

    io_opts = parser.add_argument_group('Input/output')
    io_opts.add_argument(
        "-d",
        "--directory",
        dest="directory",
        required=True,
        help="Location of Panaroo output directory",
        type=str)

    io_opts.add_argument("-o",
                         "--out_dir",
                         dest="output_dir",
                         required=True,
                         help="location of a new output directory",
                         type=str)

    io_opts.add_argument("--min_support",
                         dest="min_support",
                         help="minimum number of genomes supporting a cluster for it to be included in the database (default=1)",
                         type=int,
                         default=1)

    # Other options
    parser.add_argument("--quiet",
                        dest="quiet",
                        help="suppress additional output",
                        action='store_true',
                        default=False)

    args = parser.parse_args()
    return (args)


def main():
    args = get_options()

    # make sure trailing forward slash is present
    args.output_dir = os.path.join(args.output_dir, "")
    args.directory = os.path.join(args.directory, "")

    # check files exist
    gene_data_file = args.directory + 'gene_data.csv'
    graph_file = args.directory + 'final_graph.gml'

    if not os.path.isfile(gene_data_file):
        raise RuntimeError("Missing gene_data.csv file!")
    if not os.path.isfile(graph_file):
        raise RuntimeError("Missing final_graph.gml file!")

    # generate databse
    generate_db(gene_data_file=gene_data_file,
                graph_file=graph_file,
                outdir=args.output_dir,
                min_support=args.min_support)
    

    return


if __name__ == '__main__':
    main()
