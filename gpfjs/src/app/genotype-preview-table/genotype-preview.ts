
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
  
  get SSCfreqPercentage():string {
    if (!this.SSCfreq || this.SSCfreq == "nan") return null;
    return "SSC " + this.SSCfreq + " %";
  }
  
  get EVSfreqPercentage():string {
    if (!this.EVSfreq || this.EVSfreq == "nan") return null;
    return "EVS " + this.EVSfreq + " %";
  }
  
  get E65freqPercentage():string {
    if (!this.E65freq || this.E65freq == "nan") return null;
    return "E65 " + this.E65freq + " %";
  }
}


export class GenotypePreviewsArray {
  genotypePreviews: GenotypePreview[] = [];

  constructor(
    private total: number,
  ) {
  }
}
