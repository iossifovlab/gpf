export class PedigreeData {
  public static parsePosition(position: string): [number, number] {
    if (position !== null && position !== undefined) {
      const layout = position.split(':');
      const coordinates = layout[layout.length - 1];
      const result = coordinates.split(',').map(x => parseFloat(x));
      return result as [number, number];
    }
    return null;
  }

  public static fromArray(arr: Array<any>): PedigreeData {
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

  public constructor(
    public readonly pedigreeIdentifier: string,
    public readonly id: string,
    public readonly mother: string,
    public readonly father: string,
    public readonly gender: string,
    public readonly role: string,
    public readonly color: string,
    public readonly position: [number, number],
    public readonly generated: boolean,
    public readonly label: string,
    public readonly smallLabel: string
  ) { }
}

const KEY_TO_MAPPER: Map<string, any> = new Map([
  ['pedigree', (arr: Array<Array<any>>) => arr.map((elem) => PedigreeData.fromArray(elem))]
]);

export class GenotypePreview {
  public data = new Map<string, any>();

  public static fromJson(row: Array<any>, columns: Array<string>): GenotypePreview {
    const result = new GenotypePreview();
    // eslint-disable-next-line @typescript-eslint/no-for-in-array
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

  public get(key: string) {
    return this.data.get(key);
  }
}

export class GenotypePreviewVariantsArray {
  public genotypePreviews: GenotypePreview[] = [];

  public addPreviewVariant(row: Array<string>, columnIds: Array<string>): void {
    const genotypePreview = GenotypePreview.fromJson(row, columnIds);
    if (genotypePreview.data.size) {
      this.genotypePreviews.push(genotypePreview);
    }
  }

  public getVariantsCountFormatted(maxVariantsCount: number): string {
    let variantsCount: string;

    if (this.genotypePreviews.length > maxVariantsCount) {
      variantsCount = `more than ${maxVariantsCount} variants selected (${maxVariantsCount} shown)`;
    } else if (this.genotypePreviews.length !== 1) {
      variantsCount = `${this.genotypePreviews.length} variants selected`;
    } else {
      variantsCount = '1 variant selected';
    }

    return variantsCount;
  }

  public setGenotypePreviews(genotypePreviews: GenotypePreview[]): void {
    this.genotypePreviews = genotypePreviews;
  }
}
