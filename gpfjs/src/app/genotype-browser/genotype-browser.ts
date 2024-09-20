export class BrowserQueryFilter {
  public constructor(
    private datasetId: string,
    private geneSymbols: string[],
    public effectTypes: string[],
    public gender: string[],
    public personSetCollection: PersonSetCollection,
    private studyTypes: string[],
    public variantTypes: string[]
  ) { }

  public static fromJson(json: object): BrowserQueryFilter {
    return new BrowserQueryFilter(
      json['datasetId'] as string,
      json['geneSymbols'] as string[],
      json['effectTypes'] as string[],
      json['gender'] as string[],
      PersonSetCollection.fromJson(json['peopleGroup'] as PersonSetCollection),
      json['studyTypes'] as string[],
      json['variantTypes'] as string[]
    );
  }
}

export class PersonSetCollection {
  public constructor(
    public id: string,
    public checkedValues: string[],
  ) { }

  public static fromJson(json: object): PersonSetCollection {
    return new PersonSetCollection(
      json['id'] as string,
      json['checkedValues'] as string[]
    );
  }
}

export interface GenomicScoreInterface {
  metric: string;
  rangeStart: number;
  rangeEnd: number;
}

export class GenomicScore implements GenomicScoreInterface {
  public constructor(
    public metric: string,
    public rangeStart: number,
    public rangeEnd: number,
  ) {}

  public static fromJson(json: object): GenomicScore {
    return new GenomicScore(
      json['metric'] as string,
      json['rangeStart'] as number,
      json['rangeEnd'] as number,
    );
  }

  public static fromJsonArray(json: object): Array<GenomicScore> {
    if (!json) {
      return [];
    }

    return Object.values(json).map(arr => GenomicScore.fromJson(arr));
  }
}
