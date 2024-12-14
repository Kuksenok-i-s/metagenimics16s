import logging
from os import makedirs
from pathlib import Path

from qiime2 import Metadata, Artifact, Visualization
import qiime2.plugins.metadata.actions as metadata_actions
import qiime2.plugins.demux.actions as demux_actions
import qiime2.plugins.dada2.actions as dada2_actions
import qiime2.plugins.phylogeny.actions as phylogeny_actions
import qiime2.plugins.diversity.actions as diversity_actions
import qiime2.plugins.feature_classifier.actions as feature_classifier_actions
import qiime2.plugins.taxa.actions as taxa_actions
import qiime2.plugins.composition.actions as composition_actions

logger = logging.getLogger("DataHandler")


class ExecutionHandler:
    def __init__(self, config, action: str):
        self.config = config

        data = self.config["actions"][action]["data"]
        self.seqs_path = Path(data["data_source"]) / data["qza_sequences"]
        self.metadata_path = Path(data["data_source"]) / data["metadata"]
        self.classifier_path = Path(data["data_source"]) / data["classifier"]

        self.trim_left = self.config["qiime_params"]["dada2_params"]["params"]["trim_left"]
        self.trunc_len = self.config["qiime_params"]["dada2_params"]["params"]["trunc_len"]
        self.sampling_depth = self.config["qiime_params"]["diversity_params"]["params"]["sampling_depth"]

        self.seqs = Artifact.load(self.seqs_path)
        self.sample_metadata = Metadata.load(self.metadata_path)
        self.classifier = Artifact.load(self.classifier_path)

        self.output_dir = Path(data["data_source"]) / 'workflow_output'
        makedirs(self.output_dir, exist_ok=True)

    def demultiplex_sequences(self):
        barcode_sequence = self.sample_metadata.get_column("barcode-sequence")
        demux, demux_details = demux_actions.emp_single(seqs=self.seqs, barcodes=barcode_sequence)
        demux_summary, = demux_actions.summarize(data=demux)
        logger.info("Demultiplexing complete.")
        return demux, demux_summary

    def quality_control_dada2(self, demux):
        table, rep_seqs, stats = dada2_actions.denoise_single(
            demultiplexed_seqs=demux,
            trim_left=self.trim_left,
            trunc_len=self.trunc_len,
        )
        stats_viz, = metadata_actions.tabulate(input=stats.view(Metadata))
        logger.info("DADA2 quality control complete.")
        return table, rep_seqs, stats, stats_viz

    def phylogenetic_analysis(self, rep_seqs):
        results = phylogeny_actions.align_to_tree_mafft_fasttree(sequences=rep_seqs)
        logger.info("Phylogenetic tree generation complete.")
        return results.alignment, results.masked_alignment, results.tree, results.rooted_tree

    def diversity_analysis(self, table, rooted_tree):
        results = diversity_actions.core_metrics_phylogenetic(
            phylogeny=rooted_tree,
            table=table,
            sampling_depth=self.sampling_depth,
            metadata=self.sample_metadata,
        )
        logger.info("Diversity analysis complete.")
        return results

    def taxonomic_analysis(self, rep_seqs, table):
        taxonomy, = feature_classifier_actions.classify_sklearn(classifier=self.classifier, reads=rep_seqs)
        taxonomy_viz, = metadata_actions.tabulate(input=taxonomy.view(Metadata))
        barplot_viz, = taxa_actions.barplot(table=table, taxonomy=taxonomy, metadata=self.sample_metadata)
        logger.info("Taxonomic analysis complete.")
        return taxonomy, taxonomy_viz, barplot_viz

    def differential_abundance_analysis(self, table, grouping_field, level=None):
        if level:
            table, = taxa_actions.collapse(table=table, taxonomy=self.classifier, level=level)
        result, = composition_actions.ancombc(
            table=table,
            metadata=self.sample_metadata,
            formula=grouping_field
        )
        logger.info("Differential abundance testing complete.")
        return result

    def run_workflow(self, save_all_results: bool = True):
        demux, demux_summary = self.demultiplex_sequences()
        table, rep_seqs, stats, stats_viz = self.quality_control_dada2(demux)
        alignment, masked_alignment, unrooted_tree, rooted_tree = self.phylogenetic_analysis(rep_seqs)
        diversity_results = self.diversity_analysis(table, rooted_tree)
        taxonomy, taxonomy_viz, barplot_viz = self.taxonomic_analysis(rep_seqs, table)
        diff_abundance = self.differential_abundance_analysis(table, 'subject')

        entities_to_return = {
            'demux': demux,
            'demux_summary': demux_summary,  # Visualization
            'table': table,
            'rep_seqs': rep_seqs,
            'stats': stats,
            'stats_viz': stats_viz,  # Visualization
            'alignment': alignment,
            'masked_alignment': masked_alignment,
            'unrooted_tree': unrooted_tree,
            'rooted_tree': rooted_tree,
            'diversity_results': diversity_results,  # Results, mixed
            'taxonomy': taxonomy,
            'taxonomy_viz': taxonomy_viz,  # Visualization
            'barplot_viz': barplot_viz,  # Visualization
            'diff_abundance': diff_abundance
        }

        if save_all_results:
            for name, entity in entities_to_return.items():
                if name == 'diversity_results':  # Results class instance (qiime2/sdk/results.py)
                    for sub_entity, sub_name in zip(entity, entity._fields):
                        self._save_entity(sub_entity, sub_name)
                else:
                    self._save_entity(entity, name)

        return entities_to_return

    def _save_entity(self, entity, name):
        if isinstance(entity, Artifact):
            out_file = f'{name}.qza'
        elif isinstance(entity, Visualization):
            out_file = f'{name}.qzv'
        out_path = self.output_dir / out_file
        entity.save(out_path)

