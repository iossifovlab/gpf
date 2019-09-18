export class PedigreeData {

  static parsePosition(position: string) {
    if (position != null) {
      const result = position.split(',').map(x => parseFloat(x));
      return result as [number, number];
    }
    return null;
  }

  static fromArray(arr: Array<any>): PedigreeData {
    return new PedigreeData(
      arr[0],
      arr[1],
      arr[2],
      arr[3],
      arr[4],
      arr[5],
      arr[6],
      PedigreeData.parsePosition(arr[7]),
      arr[8],
      arr[9],
      arr[10]
    );
  }

  constructor(
    readonly pedigreeIdentifier: string,
    readonly id: string,
    readonly father: string,
    readonly mother: string,
    readonly gender: string,
    readonly role: string,
    readonly color: string,
    readonly position: [number, number],
    readonly generated: boolean,
    readonly label: string,
    readonly smallLabel: string
  ) { }

}

const KEY_TO_MAPPER: Map<string, any> = new Map([
  ['genotype', (arr: Array<Array<any>>) => arr.map((elem) => PedigreeData.fromArray(elem))]
]);

export class GenotypePreview {
  data: any = new Map<string, any>();

  static fromJson(row: string, json: any): GenotypePreview {
    const result = new GenotypePreview();
    for (const elem in json.rows[row]) {
      if (json.rows[row].hasOwnProperty(elem)) {
        const mapper = KEY_TO_MAPPER.get(json.cols[elem]);
        const propertyValue = json.rows[row][elem];

        if (mapper) {
          result.data[json.cols[elem]] = mapper(propertyValue);
        } else if (propertyValue !== 'nan' && propertyValue !== '') {
          result.data[json.cols[elem]] = propertyValue;
        }
      }
    }

    return result;
  }

  get(key: string): any {
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

    const genotypePreviewsArray = new GenotypePreviewsArray(json.count, json.legend);

    for (const row in json.rows) {
      if (json.rows.hasOwnProperty(row)) {
        const genotypePreview = GenotypePreview.fromJson(row, json);
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
