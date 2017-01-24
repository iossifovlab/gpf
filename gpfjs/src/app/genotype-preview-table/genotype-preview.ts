
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
  parentRaces: string;
  childrenDescription: string;
  probandVerbalIQ: string;
  porbandNonVerbalIQ: string;
  validationStatus: string;
  pedigree: string;
  phenoInChS: string;

  constructor(
  ) {
  }
}


export class GenotypePreviewsArray {
  genotypePreviews: GenotypePreview[] = [];

  constructor(
    private total: number,
  ) {
  }
}
