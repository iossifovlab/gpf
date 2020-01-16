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

  static fromJson(row: Array<any>, columns: Array<string>): GenotypePreview {
    const result = new GenotypePreview();
    for (const elem in row) {
      if (row.hasOwnProperty(elem)) {
        const mapper = KEY_TO_MAPPER.get(columns[elem]);
        const propertyValue = row[elem];

        if (mapper) {
          result.data.set(columns[elem], mapper(propertyValue));
        } else if (propertyValue !== 'nan' && propertyValue !== '') {
          result.data.set(columns[elem], propertyValue);
        }
      }
    }

    return result;
  }

  get(key: string): any {
    return this.data.get(key);
  }

}

export class GenotypePreviewInfo {

  static fromJson(json: any): GenotypePreviewInfo {
    const genotypePreviewInfo = new GenotypePreviewInfo(
      json.cols, json.legend, json.maxVariantsCount
    );

    return genotypePreviewInfo;
  }

  constructor(
    readonly columns: Array<string>,
    readonly legend: Array<any>,
    readonly maxVariantsCount: Number
  ) { }
}

export class GenotypePreviewVariantsArray {
  genotypePreviews: GenotypePreview[] = [];
  moreThan: Boolean = false;

  constructor() { }

  addPreviewVariant(row: Array<string>, genotypePreviewInfo: GenotypePreviewInfo) {
    if (this.genotypePreviews.length === genotypePreviewInfo.maxVariantsCount) {
      this.moreThan = true;
      return;
    }
    const genotypePreview = GenotypePreview.fromJson(row, genotypePreviewInfo.columns);
    if (genotypePreview.data.size) {
      this.genotypePreviews.push(genotypePreview);
    }
  }

  variantsCount() {
    const total = this.moreThan ? 'more than 1000' : this.genotypePreviews.length;
    return `${total} variants selected (${this.genotypePreviews.length} shown)`;
  }
}
