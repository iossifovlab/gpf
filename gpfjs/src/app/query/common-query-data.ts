import { GeneSetsState } from '../gene-sets/gene-sets-state';
import { GeneSymbolsState } from '../gene-symbols/gene-symbols';
import { GeneWeightsState } from '../gene-weights/gene-weights-store';

export interface GeneSetState {
  geneSetsCollection: string;
  geneSet: string;
  geneSetsTypes?: string[];
}


export class CommonQueryData {
  geneSymbols: string[];
  geneWeights: GeneWeightsState;
  geneSet: GeneSetState;
  datasetId: string;

  protected static prepareDatasetId(state: any): string {
    return state.datasets.selectedDataset.id;
  }

  protected static prepareGeneSymbols(state: any): string[] {
    let geneSymbols: GeneSymbolsState = state.geneSymbols;
    let result = geneSymbols.geneSymbols
      .split(/[,\s]/)
      .filter(s => s !== '')
      .map(s => s.toUpperCase());
    return result;
  }

  protected static prepareGeneSet(state: any): GeneSetState {
    let geneSetsState: GeneSetsState = state.geneSets;
    if (!geneSetsState.geneSetsCollection ||
      !geneSetsState.geneSet) {
      return {
        geneSetsCollection: null,
        geneSet: null
      };
    }
    let geneSetsTypes = Array
      .from(geneSetsState.geneSetsTypes)
      .map(t => t.id);
    return {
      geneSetsCollection: geneSetsState.geneSetsCollection.name,
      geneSet: geneSetsState.geneSet.name,
      geneSetsTypes: geneSetsTypes
    };
  }

  protected static prepareGeneWeights(state: any): GeneWeightsState {
    return state.geneWeights;
  }


}
