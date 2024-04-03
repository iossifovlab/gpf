export class FullEffectDetails {
  public constructor(
    public familyId: string,
    public location: string,
    public effectDetails: EffectDetail[],
    public geneEffects: GeneEffects[],
    public areIncomplete: boolean) { }

  public static fromGenotypeValue(value: unknown): FullEffectDetails {
    if (value instanceof Array
        && typeof value[0] === 'string'
        && typeof value[1] === 'string'
        && typeof value[2] === 'string'
        && typeof value[3] === 'string'
    ) {
      const fullEffectDetails = new FullEffectDetails('', '', [], [], true);
      fullEffectDetails.familyId = value[0];
      fullEffectDetails.location = value[1];
      fullEffectDetails.effectDetails = EffectDetail.fromDetailValue(value[2]);

      // Check if gene and effect columns are both empty
      for (const ed of fullEffectDetails.effectDetails) {
        // Equal only when both are 'None'
        if (ed.gene !== ed.effect) {
          fullEffectDetails.areIncomplete = false;
          break;
        }
      }

      fullEffectDetails.geneEffects = GeneEffects.fromEffectValue(value[3]);

      return fullEffectDetails;
    }
  }
}

export class EffectDetail {
  public constructor(
    public gene: string,
    public transcript: string,
    public effect: string,
    public details: string) { }

  public static fromDetailValue(value: string): EffectDetail[] {
    return value.split('|').map(detail => {
      const details = detail.split(':');
      return {
        gene: details[1],
        transcript: details[0],
        effect: details[2],
        details: details[3],
      };
    }).sort((e1, e2) => {
      if (e1.gene < e2.gene) {
        return -1;
      }
      if (e1.gene > e2.gene) {
        return 1;
      }
      return 0;
    });
  }
}

export class GeneEffects {
  public constructor(
    public gene: string,
    public effect: string) { }

  public static fromEffectValue(value: string): GeneEffects[] {
    return value.split('|').map(geneEffect => {
      const effect = geneEffect.split(':');
      return {
        gene: effect[0],
        effect: effect[1],
      };
    });
  }
}
