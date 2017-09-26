const enum Gender {
  MALE = 1,
  FEMALE = 2
}

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

let FIELD_TO_OBJECT_PROPERTY: Map<string, string> = new Map([
  ['family id', 'familyId'],
  ['study', 'study'],
  ['study phenotype', 'studyPhenotype'],
  ['location', 'location'],
  ['variant', 'variant'],
  ['family genotype', 'familyGenotype'],
  ['from parent', 'fromParent'],
  ['in child', 'inChild'],
  ['worst requested effect', 'worstRequestedEffect'],
  ['genes', 'genes'],
  ['count', 'count'],
  ['all effects', 'allEffects'],
  ['requested effects', 'requestedEffects'],
  ['population type', 'populationType'],
  ['worst effect type', 'worstEffectType'],
  ['effect details', 'effectDetails'],
  ['alternative allele frequency', 'alternativeAlleleFrequency'],
  ['number of alternative alleles', 'alternativeAllelesCount'],
  // ['SSCfreq', 'SSCfreqWithoutNan'],
  // ['EVSfreq', 'EVSfreqWithoutNan'],
  // ['E65freq', 'E65freqWithoutNan'],
  ['number of genotyped parents', 'genotypedParentsCount'],
  ['children description', 'childrenDescription'],
  ['validation status', 'validationStatus'],
  ['_pedigree_', 'pedigreeDataFromArray'],
  ['phenoInChS', 'phenoInChS']
]);

export class GenotypePreview {
  familyId: string;
  study: string;
  studyPhenotype: string;
  location: string;
  variant: string;
  familyGenotype: string;
  fromParent: string;
  inChild: string;
  worstRequestedEffect: string;
  genes: string;
  count: string;
  allEffects: string;
  requestedEffects: string;
  populationType: string;
  worstEffectType: string;
  effectDetails: string;
  alternativeAlleleFrequency: string;
  alternativeAllelesCount: string;
  SSCfreq: string | null;
  EVSfreq: string | null;
  E65freq: string | null;
  genotypedParentsCount: string;
  motherRace: string;
  fatherRace: string;
  childrenDescription: string;
  probandVerbalIQ: string;
  probandNonVerbalIQ: string;
  validationStatus: string;
  pedigree: PedigreeData[];
  phenoInChS: string;
  additionalData: any = new Map<string, any>();

  static fromJson(row: string, json: any): GenotypePreview {
    let result = new GenotypePreview();
    for (let elem in json.rows[row]) {
      if (json.rows[row].hasOwnProperty(elem)) {
        let propertyName = FIELD_TO_OBJECT_PROPERTY.get(json.cols[elem]);
        let propertyValue = json.rows[row][elem];

        if (propertyName) {
          result[propertyName] = propertyValue;
      } else if (propertyValue !== 'nan' && propertyValue !== '') {
          result.additionalData[json.cols[elem]] = propertyValue;
        }
      }
    }

    return result;
  }

  constructor(
  ) {
  }

  get parentRaces(): string {
    return this.motherRace + ':' + this.fatherRace;
  }

  set parentRaces(parentRaces: string) {
    let result = parentRaces.split(':');
    if (result.length !== 2) {
      return;
    }

    this.motherRace = result[0];
    this.fatherRace = result[1];
  }

  set SSCfreqWithoutNan(SSCfreqString: string) {
    if (SSCfreqString === 'nan' || SSCfreqString === '') {
      this.SSCfreq = null;
    } else {
      this.SSCfreq = SSCfreqString;
    }
  }

  set EVSfreqWithoutNan(EVSfreqString: string) {
    if (EVSfreqString === 'nan' || EVSfreqString === '') {
      this.EVSfreq = null;
    } else {
      this.EVSfreq = EVSfreqString;
    }
  }

  set E65freqWithoutNan(E65freqString: string) {
    if (E65freqString === 'nan' || E65freqString === '') {
      this.E65freq = null;
    } else {
      this.E65freq = E65freqString;
    }
  }

  set pedigreeDataFromArray(arr: Array<Array<any> >) {
    this.pedigree = arr.map((elem) => PedigreeData.fromArray(elem));
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
