import { BrowserQueryFilter } from 'app/genotype-browser/genotype-browser';

export class ChildrenStats {
  public static fromJson(json: object): ChildrenStats {
    return new ChildrenStats(
      json['M'] as number,
      json['F'] as number,
      json['U'] as number
    );
  }

  public constructor(
    public readonly male: number,
    public readonly female: number,
    public readonly unspecified: number
  ) { }
}

export class EnrichmentTestResult {
  public static fromJson(json: object): EnrichmentTestResult {
    return new EnrichmentTestResult(
      json['name'] as string,
      json['count'] as number,
      json['expected'] as number,
      json['overlapped'] as number,
      json['pvalue'] as number,
      BrowserQueryFilter.fromJson(json['countFilter']),
      BrowserQueryFilter.fromJson(json['overlapFilter'])
    );
  }

  public constructor(
    public readonly name: string,
    public readonly count: number,
    public readonly expected: number,
    public readonly overlapped: number,
    public readonly pvalue: number,
    public readonly countFilter: BrowserQueryFilter,
    public readonly overlapFilter: BrowserQueryFilter
  ) { }
}

export class EnrichmentEffectResult {
  public static fromJson(json: object): EnrichmentEffectResult {
    return new EnrichmentEffectResult(
      EnrichmentTestResult.fromJson(json['all'] as object),
      EnrichmentTestResult.fromJson(json['male'] as object),
      EnrichmentTestResult.fromJson(json['female'] as object)
    );
  }

  public constructor(
    public readonly all: EnrichmentTestResult,
    public readonly male: EnrichmentTestResult,
    public readonly female: EnrichmentTestResult
  ) { }
}

export class EnrichmentResult {
  public static fromJsonArray(jsonArray: object[]): Array<EnrichmentResult> {
    return jsonArray.map((json) => EnrichmentResult.fromJson(json));
  }

  public static fromJson(json: object): EnrichmentResult {
    return new EnrichmentResult(
      json['selector'] as string,
      EnrichmentEffectResult.fromJson(json['LGDs'] as object),
      EnrichmentEffectResult.fromJson(json['missense'] as object),
      EnrichmentEffectResult.fromJson(json['synonymous'] as object),
      ChildrenStats.fromJson(json['childrenStats'] as object)
    );
  }
  public constructor(
    public readonly selector: string,
    public readonly LGDs: EnrichmentEffectResult,
    public readonly missense: EnrichmentEffectResult,
    public readonly synonymous: EnrichmentEffectResult,
    public readonly childrenStats: ChildrenStats
  ) { }
}

export class EnrichmentResults {
  public static fromJson(json: object): EnrichmentResults {
    return new EnrichmentResults(
      json['desc'] as string,
      EnrichmentResult.fromJsonArray(json['result'] as object[])
    );
  }

  public constructor(
    public readonly description: string,
    public readonly results: Array<EnrichmentResult>
  ) { }
}
