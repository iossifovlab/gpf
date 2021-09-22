export class BrowserQueryFilter {
  constructor(
    private datasetId: string,
    private geneSymbols: string[],
    private effectTypes: string[],
    private gender: string[],
    private personSetCollection: PersonSetCollection,
    private studyTypes: string[],
    private variantTypes: string[],
    private genomicScores: GenomicScore[],
    private presentInParent: PresentInParent,
    private presentInChild: string[],
  ) { }
}

export class PersonSetCollection {
  constructor(
    private id: string,
    private checkedValues: string[],
  ) { }
}

export class GenomicScore {
  constructor(
    private metric: string,
    private rangeStart: number,
    private rangeEnd: number,
  ) {}
}

export class PresentInParent {
  constructor(
    private presentInParent: string[],
    private rarity: PresentInParentRarity,
  ) { }
}

export class PresentInParentRarity {
  constructor(
    private minFreq: number,
    private maxFreq: number,
    private ultraRare: boolean,
  ) { }
}
