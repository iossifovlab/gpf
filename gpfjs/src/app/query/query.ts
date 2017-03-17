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


export class QueryData {
  public static trueFalseToStringArray(obj: any): string[] {
    let values = Array<string>();
    for (let key of Object.keys(obj)) {
      if (obj[key]) {
        values.push(key);
      }
    }
    return values;
  }
}
