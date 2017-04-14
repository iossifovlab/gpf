export class PhenoToolResult {
  constructor(
    readonly count: number,
    readonly deviation: number,
    readonly mean: number,
  ) { }

  get rangeStart() {
    return this.mean - this.deviation;
  }

  get rangeEnd() {
    return this.mean + this.deviation;
  }

  static fromJson(json: any): PhenoToolResult {
    return new PhenoToolResult(
      json['count'],
      json['deviation'],
      json['mean'],
    );
  }
}


export class PhenoToolResultsPerGender {
  constructor(
    readonly positive: PhenoToolResult,
    readonly negative: PhenoToolResult,
    readonly pValue: number,
  ) { }

  static fromJson(json: any): PhenoToolResultsPerGender {
    return new PhenoToolResultsPerGender(
      PhenoToolResult.fromJson(json['positive']),
      PhenoToolResult.fromJson(json['negative']),
      json['pValue'],
    );
  }
}

export class PhenoToolResultsPerEffect {
  constructor(
    readonly effect: string,
    readonly maleResult: PhenoToolResultsPerGender,
    readonly femaleResult: PhenoToolResultsPerGender
  ) { }

  static fromJson(json: any): PhenoToolResultsPerEffect {
    return new PhenoToolResultsPerEffect(
      json['effect'],
      PhenoToolResultsPerGender.fromJson(json['maleResults']),
      PhenoToolResultsPerGender.fromJson(json['femaleResults']),
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<PhenoToolResultsPerEffect> {
    return jsonArray.map((json) => PhenoToolResultsPerEffect.fromJson(json));
  }
}

export class PhenoToolResults {
  constructor(
    readonly description: string,
    readonly results: Array<PhenoToolResultsPerEffect>
  ) { }

  static fromJson(json: any): PhenoToolResults {
    return new PhenoToolResults(
      json['description'],
      PhenoToolResultsPerEffect.fromJsonArray(json['results'])
    );
  }
}
