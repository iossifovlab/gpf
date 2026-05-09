export class PhenoToolResult {
  public constructor(
    public readonly count: number,
    public readonly deviation: number,
    public readonly mean: number,
  ) { }

  public get rangeStart(): number {
    return this.mean - this.deviation;
  }

  public get rangeEnd(): number {
    return this.mean + this.deviation;
  }

  public static fromJson(json: object): PhenoToolResult {
    return new PhenoToolResult(
      json['count'] as number,
      json['deviation'] as number,
      json['mean'] as number,
    );
  }
}

export class PhenoToolResultsPerGender {
  public constructor(
    public readonly positive: PhenoToolResult,
    public readonly negative: PhenoToolResult,
    public readonly pValue: number,
  ) { }

  public static fromJson(json: object): PhenoToolResultsPerGender {
    return new PhenoToolResultsPerGender(
      PhenoToolResult.fromJson(json['positive'] as object),
      PhenoToolResult.fromJson(json['negative'] as object),
      json['pValue'] as number,
    );
  }
}

export class PhenoToolResultsPerEffect {
  public constructor(
    public readonly effect: string,
    public readonly maleResult: PhenoToolResultsPerGender,
    public readonly femaleResult: PhenoToolResultsPerGender
  ) { }

  public static fromJson(json: object): PhenoToolResultsPerEffect {
    return new PhenoToolResultsPerEffect(
      json['effect'] as string,
      PhenoToolResultsPerGender.fromJson(json['maleResults'] as object),
      PhenoToolResultsPerGender.fromJson(json['femaleResults'] as object),
    );
  }

  public static fromJsonArray(jsonArray: object[]): Array<PhenoToolResultsPerEffect> {
    return jsonArray.map((json) => PhenoToolResultsPerEffect.fromJson(json));
  }
}

export class PhenoToolResults {
  public constructor(
    public readonly description: string,
    public readonly results: Array<PhenoToolResultsPerEffect>
  ) { }

  public static fromJson(json: object): PhenoToolResults {
    return new PhenoToolResults(
      json['description'] as string,
      PhenoToolResultsPerEffect.fromJsonArray(json['results'] as object[])
    );
  }
}
