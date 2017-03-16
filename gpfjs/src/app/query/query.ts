import { GenotypeBrowser } from '../datasets/datasets';
import { GeneSetsState } from '../gene-sets/gene-sets-state';
import { GeneSymbolsState } from '../gene-symbols/gene-symbols';
import { GeneWeightsState } from '../gene-weights/gene-weights-store';
import { PresentInParentState } from '../present-in-parent/present-in-parent';
import { CommonQueryData } from './common-query-data';

export interface Rarity {
  ultraRare: boolean;
  minFreq: number;
  maxFreq: number;
};

export interface GeneSetState {
  geneSetsCollection: string;
  geneSet: string;
  geneSetsTypes?: string[];
}

export interface PedigreeSelectorState {
  id: string;
  checkedValues: string[];
}


export class QueryData extends CommonQueryData {
  effectTypes: string;
  gender: string[];
  presentInChild: string[];
  presentInParent: any;
  rarity: Rarity;
  variantTypes: string[];
  pedigreeSelector: PedigreeSelectorState;
  regions: string[];

  private static prepareEffectTypes(state: any): string {
    return state.effectTypes;
  }
  public static trueFalseToStringArray(obj: any): string[] {
    let values = Array<string>();
    for (let key of Object.keys(obj)) {
      if (obj[key]) {
        values.push(key);
      }
    }
    return values;
  }
  private static prepareGender(state: any): string[] {
    return QueryData.trueFalseToStringArray(state.gender);
  }
  private static prepareVariantTypes(state: any): string[] {
    return QueryData.trueFalseToStringArray(state.variantTypes);
  }
  private static getGenotypeBrowser(state): GenotypeBrowser {
    return state.datasets.selectedDataset.genotypeBrowser;
  }
  private static preparePresentInChild(state: any): string[] {
    if (!QueryData.getGenotypeBrowser(state).hasPresentInChild) {
      return null;
    }
    return state.presentInChild;
  }
  private static preparePresentInParent(state: any): string[] {
    if (!QueryData.getGenotypeBrowser(state).hasPresentInParent) {
      return null;
    }

    let presentInParentState: PresentInParentState = state.presentInParent;

    let result = new Array<string>();
    if (presentInParentState.fatherOnly) {
      result.push('father only');
    }
    if (presentInParentState.motherOnly) {
      result.push('mother only');
    }
    if (presentInParentState.motherFather) {
      result.push('mother and father');
    }
    if (presentInParentState.neither) {
      result.push('neither');
    }
    return result;
  }

  private static prepareRarity(state: any): Rarity {
    if (!QueryData.getGenotypeBrowser(state).hasPresentInParent) {
      return null;
    }

    let presentInParentState: PresentInParentState = state.presentInParent;
    let rarity: Rarity = {
      ultraRare: presentInParentState.ultraRare,
      minFreq: presentInParentState.rarityIntervalStart,
      maxFreq: presentInParentState.rarityIntervalEnd
    };
    if (rarity.ultraRare) {
      rarity.minFreq = null;
      rarity.maxFreq = null;
    } else {
      rarity.ultraRare = null;
      if (rarity.minFreq <= 0.0) {
        rarity.minFreq = null;
      }
      if (rarity.maxFreq >= 100.0) {
        rarity.maxFreq = null;
      }
    }
    return rarity;
  }

  private static preparePedigreeSelector(state: any): PedigreeSelectorState {
    if (!QueryData.getGenotypeBrowser(state).hasPedigreeSelector) {
      return null;
    }
    return {
      id: state.pedigreeSelector.pedigree.id,
      checkedValues: state.pedigreeSelector.checkedValues
    };
  }

  private static prepareRegionsFilter(state: any): string[] {
    let regionsFilter: string = state.regionsFilter.regionsFilter;
    let result = regionsFilter
      .split(/[\s]/)
      .map(s => s.replace(/[,]/g, ''))
      .filter(s => s !== '');
    if (result.length === 0) {
      return null;
    }
    return result;
  }

  static prepare(state: any): QueryData {
    let query = new QueryData();

    query.datasetId = QueryData.prepareDatasetId(state);
    query.effectTypes = QueryData.prepareEffectTypes(state);
    query.gender = QueryData.prepareGender(state);
    query.variantTypes = QueryData.prepareVariantTypes(state);
    query.presentInChild = QueryData.preparePresentInChild(state);
    query.presentInParent = QueryData.preparePresentInParent(state);
    query.rarity = QueryData.prepareRarity(state);
    query.pedigreeSelector = QueryData.preparePedigreeSelector(state);
    query.geneSymbols = QueryData.prepareGeneSymbols(state);
    query.geneSet = QueryData.prepareGeneSet(state);
    query.geneWeights = QueryData.prepareGeneWeights(state);
    query.regions = QueryData.prepareRegionsFilter(state);

    return query;
  }

}
