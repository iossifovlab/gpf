export interface Rarity {
  ultraRare: boolean;
  minFreq: number;
  maxFreq: number;
};

export class QueryData {
  effectTypes: string;
  gender: string[];
  presentInChild: string[];
  presentInParent: any;
  rarity: Rarity;
  variantTypes: string[];
  geneSymbols: string[];
  datasetId: string;
  pedigreeSelector: any;
}
