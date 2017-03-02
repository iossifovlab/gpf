export class ChildrenStats {
  constructor(
    readonly male: number,
    readonly female: number
  ) { }

  static fromJson(json: any): ChildrenStats {
    return new ChildrenStats(
      json['M'],
      json['F']
    );
  }
}

export class EnrichmentTestResult {
  constructor(
    readonly name: string,
    readonly count: number,
    readonly expected: number,
    readonly overlapped: number,
    readonly pvalue: number
  ) { }

  static fromJson(json: any): EnrichmentTestResult {
    return new EnrichmentTestResult(
      json['name'],
      json['count'],
      json['expected'],
      json['overlapped'],
      json['pvalue']
    );
  }
}


export class EnrichmentEffectResult {
  constructor(
    readonly all: EnrichmentTestResult,
    readonly male: EnrichmentTestResult,
    readonly female: EnrichmentTestResult,
    readonly rec: EnrichmentTestResult
  ) { }

  static fromJson(json: any): EnrichmentEffectResult {
    return new EnrichmentEffectResult(
      EnrichmentTestResult.fromJson(json['all']),
      EnrichmentTestResult.fromJson(json['male']),
      EnrichmentTestResult.fromJson(json['female']),
      EnrichmentTestResult.fromJson(json['rec'])
    );
  }
}

export class EnrichmentResult {
  constructor(
    readonly selector: string,
    readonly LGDs: EnrichmentEffectResult,
    readonly missense: EnrichmentEffectResult,
    readonly synonymous: EnrichmentEffectResult,
    readonly childrenStats: ChildrenStats
  ) { }

  static fromJson(json: any): EnrichmentResult {
    return new EnrichmentResult(
      json['selector'],
      EnrichmentEffectResult.fromJson(json['LGDs']),
      EnrichmentEffectResult.fromJson(json['missense']),
      EnrichmentEffectResult.fromJson(json['synonymous']),
      ChildrenStats.fromJson(json['childrenStats'])
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<EnrichmentResult> {
    return jsonArray.map((json) => EnrichmentResult.fromJson(json));
  }
}

export class EnrichmentResults {
  constructor(
    readonly description: string,
    readonly results: Array<EnrichmentResult>
  ) { }

  static fromJson(json: any): EnrichmentResults {
    return new EnrichmentResults(
      json['desc'],
      EnrichmentResult.fromJsonArray(json['result'])
    );
  }
}
