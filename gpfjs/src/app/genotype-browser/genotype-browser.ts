export class BrowserQueryFilter {
  constructor(
    private datasetId: string,
    private geneSymbols: string[],
    private effectTypes: string[],
    private gender: string[],
    private peopleGroup: PeopleGroup,
    private studyTypes: string[],
    private variantTypes: string[],
  ) { }
}

export class PeopleGroup {
  constructor(
    private id: string,
    private checkedValues: string[],
  ) { }
}
