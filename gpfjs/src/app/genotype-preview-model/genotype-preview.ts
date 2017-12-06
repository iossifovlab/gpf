export class PedigreeData {

  static fromArray(arr: Array<any>): PedigreeData {
    return new PedigreeData(
      arr[0],
      arr[1],
      arr[2],
      arr[3],
      arr[4],
      arr[5],
      arr[6],
      arr[7]
    );
  }

  constructor(
    readonly pedigreeIdentifier: string,
    readonly id: string,
    readonly father: string,
    readonly mother: string,
    readonly gender: string,
    readonly color: string,
    readonly label: string,
    readonly smallLabel: string
  ) { }

}

let KEY_TO_MAPPER: Map<string, any> = new Map([
  ['pedigree', (arr: Array<Array<any>>) => arr.map((elem) => PedigreeData.fromArray(elem))]
]);

export class GenotypePreview {
  data: any = new Map<string, any>();

  static fromJson(row: string, json: any): GenotypePreview {
    let result = new GenotypePreview();
    for (let elem in json.rows[row]) {
      if (json.rows[row].hasOwnProperty(elem)) {
        let mapper = KEY_TO_MAPPER.get(json.cols[elem]);
        let propertyValue = json.rows[row][elem];

        if (mapper) {
          result.data[json.cols[elem]] = mapper(propertyValue);
        } else if (propertyValue !== 'nan' && propertyValue !== '') {
          result.data[json.cols[elem]] = propertyValue;
        }
      }
    }

    return result;
  }

  get(key: string) : any {
    return this.data[key];
  }

}

export class GenotypePreviewsArray {
  genotypePreviews: GenotypePreview[] = [];

  static fromJson(json: any): GenotypePreviewsArray {
    if (json.count === 0) {
      return new GenotypePreviewsArray(0, null);
    }
    if (json.cols === undefined) {
      return new GenotypePreviewsArray(0, null);
    }

    let genotypePreviewsArray = new GenotypePreviewsArray(json.count, json.legend);

    for (let row in json.rows) {
      if (json.rows.hasOwnProperty(row)) {
        let genotypePreview = GenotypePreview.fromJson(row, json);
        genotypePreviewsArray.genotypePreviews.push(genotypePreview);
      }
    }
    return genotypePreviewsArray;
  }

  constructor(
    readonly total: number,
    readonly legend: Array<any>
  ) {
  }
}
