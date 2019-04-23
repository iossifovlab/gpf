export interface Rarity {
  ultraRare: boolean;
  minFreq: number;
  maxFreq: number;
}

export interface GeneSetState {
  geneSetsCollection: string;
  geneSet: string;
  geneSetsTypes?: string[];
}

export class QueryData {
  public static trueFalseToStringArray(obj: any): string[] {
    const values = Array<string>();
    for (const key of Object.keys(obj)) {
      if (obj[key]) {
        values.push(key);
      }
    }
    return values;
  }
}
