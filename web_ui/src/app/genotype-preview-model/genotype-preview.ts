// Wire format for a single PedigreeData row: a positional array whose
// shape is fixed by the backend's family-counter response. Index 7 is a
// "row:col,row:col" position string; everything else is a plain field.
export type PedigreeDataArray = [
  pedigreeIdentifier: string,
  id: string,
  mother: string,
  father: string,
  gender: string,
  role: string,
  color: string,
  position: string,
  generated: boolean,
  label: string,
  smallLabel: string,
];

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

  public static fromArray(arr: readonly unknown[]): PedigreeData {
    const tuple = arr as PedigreeDataArray;
    return new PedigreeData(
      tuple[0],
      tuple[1],
      tuple[2],
      tuple[3],
      tuple[4],
      tuple[5],
      tuple[6],
      PedigreeData.parsePosition(tuple[7]),
      tuple[8],
      tuple[9],
      tuple[10]
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

type ColumnMapper = (value: unknown) => unknown;

const KEY_TO_MAPPER = new Map<string, ColumnMapper>([
  ['pedigree', (value) =>
    (value as PedigreeDataArray[]).map((elem) => PedigreeData.fromArray(elem)),
  ],
]);

export class GenotypePreview {
  public data = new Map<string, unknown>();

  public static fromJson(row: readonly unknown[], columns: readonly string[]): GenotypePreview {
    const result = new GenotypePreview();
    for (let i = 0; i < row.length; i++) {
      const mapper = KEY_TO_MAPPER.get(columns[i]);
      const propertyValue = row[i];

      if (mapper) {
        result.data.set(columns[i], mapper(propertyValue));
      } else if (propertyValue !== 'nan' && propertyValue !== '') {
        result.data.set(columns[i], propertyValue);
      }
    }
    return result;
  }

  public get(key: string): unknown {
    return this.data.get(key);
  }
}

export class GenotypePreviewVariantsArray {
  public genotypePreviews: GenotypePreview[] = [];

  public addPreviewVariant(row: readonly unknown[], columnIds: readonly string[]): void {
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
