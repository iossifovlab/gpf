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
  static prepare(state: any): EnrichmentQueryData {
    let query = new EnrichmentQueryData();

    query.datasetId = EnrichmentQueryData.prepareDatasetId(state);
    query.geneSymbols = EnrichmentQueryData.prepareGeneSymbols(state);
    query.geneSet = EnrichmentQueryData.prepareGeneSet(state);
    query.geneWeights = EnrichmentQueryData.prepareGeneWeights(state);

    return query;
  }

}
