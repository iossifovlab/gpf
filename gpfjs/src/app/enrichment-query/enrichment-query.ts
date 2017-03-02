import { GeneSetsState } from '../gene-sets/gene-sets-state';
import { GeneSymbolsState } from '../gene-symbols/gene-symbols';
import { GeneWeightsState } from '../gene-weights/gene-weights-store';
import { CommonQueryData } from '../query/common-query-data';

export interface GeneSetState {
  geneSetsCollection: string;
  geneSet: string;
  geneSetsTypes?: string[];
}


export class EnrichmentQueryData extends CommonQueryData {
  enrichmentBackgroundModel: string;
  enrichmentCountingModel: string;

  protected static prepareEnrichmentBackgroundModel(state: any): string {
    if (!state || !state.enrichmentModels || !state.enrichmentModels.background) {
      return null;
    }
    return state.enrichmentModels.background.id;
  }

  protected static prepareEnrichmentCountingModel(state: any): string {
    if (!state || !state.enrichmentModels || !state.enrichmentModels.counting) {
      return null;
    }
    return state.enrichmentModels.counting.id;
  }

  static prepare(state: any): EnrichmentQueryData {
    let query = new EnrichmentQueryData();

    query.datasetId = EnrichmentQueryData.prepareDatasetId(state);
    query.geneSymbols = EnrichmentQueryData.prepareGeneSymbols(state);
    query.geneSet = EnrichmentQueryData.prepareGeneSet(state);
    query.geneWeights = EnrichmentQueryData.prepareGeneWeights(state);

    query.enrichmentBackgroundModel = EnrichmentQueryData.prepareEnrichmentBackgroundModel(state);
    query.enrichmentCountingModel = EnrichmentQueryData.prepareEnrichmentCountingModel(state);

    return query;
  }

}
