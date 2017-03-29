const enum Gender {
  MALE = 1,
  FEMALE = 2
}

export class PedigreeData {

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
}


export class GenotypePreview {
  familyId: string;
  study: string;
  studyPhenotype: string;
  location: string;
  variant: string
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

  constructor(
  ) {
  }

  get parentRaces():string {
    return this.motherRace + ":" + this.fatherRace;
  }

  set parentRaces(parentRaces: string) {
    let result = parentRaces.split(":");
    if (result.length != 2) return;

    this.motherRace = result[0];
    this.fatherRace = result[1];
  }

  set SSCfreqWithoutNan(SSCfreqString: string) {
    if (SSCfreqString == "nan" || SSCfreqString == "") {
      this.SSCfreq = null;
    }
    else {
      this.SSCfreq = SSCfreqString;
    }
  }

  set EVSfreqWithoutNan(EVSfreqString: string) {
    if (EVSfreqString == "nan" || EVSfreqString == "") {
      this.EVSfreq = null;
    }
    else {
      this.EVSfreq = EVSfreqString;
    }
  }

  set E65freqWithoutNan(E65freqString: string) {
    if (E65freqString == "nan" || E65freqString == "") {
      this.E65freq = null;
    }
    else {
      this.E65freq = E65freqString;
    }
  }

  set pedigreeDataFromArray(arr: Array<Array<any> >) {
    this.pedigree = arr.map((elem) => PedigreeData.fromArray(elem));
  }
}


export class GenotypePreviewsArray {
  genotypePreviews: GenotypePreview[] = [];


  constructor(
    readonly total: number,
    readonly legend: Array<any>
  ) {
  }
}
