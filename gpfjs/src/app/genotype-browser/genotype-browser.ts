export class BrowserQueryFilter {
  public constructor(
    private datasetId: string,
    private geneSymbols: string[],
    private effectTypes: string[],
    private gender: string[],
    public personSetCollection: PersonSetCollection,
    private studyTypes: string[],
    private variantTypes: string[]
  ) { }

  public static fromJson(json): BrowserQueryFilter {
    return new BrowserQueryFilter(
      json['datasetId'],
      json['geneSymbols'],
      json['effectTypes'],
      json['gender'],
      PersonSetCollection.fromJson(json['peopleGroup']),
      json['studyTypes'],
      json['variantTypes']
    );
  }
}

export class PersonSetCollection {
  public constructor(
    public id: string,
    public checkedValues: string[],
  ) { }

  public static fromJson(json): PersonSetCollection {
    return new PersonSetCollection(
      json['id'],
      json['checkedValues']
    );
  }
}

export class GenomicScore {
  public constructor(
    private metric: string,
    private rangeStart: number,
    private rangeEnd: number,
  ) {}

  public static fromJson(json): GenomicScore {
    return new GenomicScore(
      json['metric'],
      json['rangeStart'],
      json['rangeEnd'],
    );
  }

  public static fromJsonArray(json: object): Array<GenomicScore> {
    if (!json) {
      return [];
    }

    return Object.values(json).map(arr => GenomicScore.fromJson(arr));
  }
}
