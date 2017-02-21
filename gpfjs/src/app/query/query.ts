import { GeneWeightsState } from '../gene-weights/gene-weights-store';

export interface Rarity {
  ultraRare: boolean;
  minFreq: number;
  maxFreq: number;
};

export interface GeneSet {
  geneSetsCollection: string;
  geneSet: string;
  geneSetsTypes?: string[];
}

export class QueryData {
  effectTypes: string;
  gender: string[];
  presentInChild: string[];
  presentInParent: any;
  rarity: Rarity;
  variantTypes: string[];
  geneSymbols: string[];
  geneWeights: GeneWeightsState;
  geneSet: GeneSet;
  datasetId: string;
  pedigreeSelector: any;
  regions: string[];
}
