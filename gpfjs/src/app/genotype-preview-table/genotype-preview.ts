
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
  SSCfreq: string;
  EVSfreq: string;
  E65freq: string;
  genotypedParentsCount: string;
  motherRace: string;
  fatherRace: string;
  childrenDescription: string;
  probandVerbalIQ: string;
  probandNonVerbalIQ: string;
  validationStatus: string;
  pedigree: string;
  phenoInChS: string;

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
}


export class GenotypePreviewsArray {
  genotypePreviews: GenotypePreview[] = [];

  constructor(
    private total: number,
  ) {
  }
}
