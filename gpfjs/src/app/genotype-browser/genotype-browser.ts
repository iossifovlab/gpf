export class BrowserQueryFilter {
  constructor(
    private datasetId: string,
    private geneSymbols: string[],
    private effectTypes: string[],
    private gender: string[],
    private peopleGroup: PeopleGroup,
    private studyTypes: string[],
    private variantTypes: string[],
    private genomicScores: GenomicScore[],
  ) { }
}

export class PeopleGroup {
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
