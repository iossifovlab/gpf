export class StudySummary {

    static columnToFieldMap = new Map<string, string>([
      ['number of siblings', 'numberOfSiblings'],
      ['number of probands', 'numberOfProbands'],
      ['families', 'families'],
      ['description', 'description'],
      ['study year', 'studyYear'],
      ['study name', 'studyName'],
      ['PubMed', 'pubMed'],
      ['transmitted', 'transmitted'],
      ['phenotype', 'phenotype'],
      ['denovo', 'denovo'],
      ['study type', 'studyType'],
    ]);

  static fromJson(json: any) {
    return new StudySummary(
      json['number of siblings'],
      json['number of probands'],
      json['families'],
      json['description'],
      json['study year'],
      json['study name'],
      json['PubMed'],
      json['transmitted'],
      json['phenotype'],
      json['denovo'],
      json['study type'],
    );
  }

  static columnNameToFieldName(columnName: string): string {
    if (StudySummary.columnToFieldMap.has(columnName)) {
      return StudySummary.columnToFieldMap.get(columnName);
    }
    return '';
  }

  constructor(
    readonly numberOfSiblings: number,
    readonly numberOfProbands: number,
    readonly families: number,
    readonly description: string,
    readonly studyYear: string,
    readonly studyName: string,
    readonly pubMed: string,
    readonly transmitted: boolean,
    readonly phenotype: string,
    readonly denovo: boolean,
    readonly studyType: string
  ) {}

}


export class StudiesSummaries {
  static fromJsonArray(json: any) {
    return new StudiesSummaries(
      json['summaries'].map(
        studySummary => StudySummary.fromJson(studySummary)),
      json['columns']
    );
  }

  constructor(
    readonly studiesSummaries: StudySummary[],
    readonly columnsOrder: string[]
  ) {}
}
