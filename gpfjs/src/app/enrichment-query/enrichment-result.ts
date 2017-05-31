import { GenotypePreview } from '../genotype-preview-table/genotype-preview';

export class GenotypePreviewWithDatasetId extends GenotypePreview {
  datasetId: string;

  static withoutDatasetId(genotypePreview: GenotypePreviewWithDatasetId): GenotypePreview {
   let result = Object.assign({}, genotypePreview);
   delete result.datasetId;
   return result;
  }


}

export class ChildrenStats {

  static fromJson(json: any): ChildrenStats {
    return new ChildrenStats(
      json['M'],
      json['F']
    );
  }

  constructor(
    readonly male: number,
    readonly female: number
  ) { }
}

export class EnrichmentTestResult {

  static fromJson(json: any): EnrichmentTestResult {
    return new EnrichmentTestResult(
      json['name'],
      json['count'],
      json['expected'],
      json['overlapped'],
      json['pvalue'],
      json['countFilter'] as GenotypePreviewWithDatasetId,
      json['overlapFilter'] as GenotypePreviewWithDatasetId,
    );
  }

  constructor(
    readonly name: string,
    readonly count: number,
    readonly expected: number,
    readonly overlapped: number,
    readonly pvalue: number,
    readonly countFilter: GenotypePreviewWithDatasetId,
    readonly overlapFilter: GenotypePreviewWithDatasetId,
  ) { }
}


export class EnrichmentEffectResult {

  static fromJson(json: any): EnrichmentEffectResult {
    return new EnrichmentEffectResult(
      EnrichmentTestResult.fromJson(json['all']),
      EnrichmentTestResult.fromJson(json['male']),
      EnrichmentTestResult.fromJson(json['female']),
      EnrichmentTestResult.fromJson(json['rec'])
    );
  }

  constructor(
    readonly all: EnrichmentTestResult,
    readonly male: EnrichmentTestResult,
    readonly female: EnrichmentTestResult,
    readonly rec: EnrichmentTestResult
  ) { }

}

export class EnrichmentResult {

  static fromJsonArray(jsonArray: Array<Object>): Array<EnrichmentResult> {
    return jsonArray.map((json) => EnrichmentResult.fromJson(json));
  }

  static fromJson(json: any): EnrichmentResult {
    return new EnrichmentResult(
      json['selector'],
      EnrichmentEffectResult.fromJson(json['LGDs']),
      EnrichmentEffectResult.fromJson(json['missense']),
      EnrichmentEffectResult.fromJson(json['synonymous']),
      ChildrenStats.fromJson(json['childrenStats'])
    );
  }
  constructor(
    readonly selector: string,
    readonly LGDs: EnrichmentEffectResult,
    readonly missense: EnrichmentEffectResult,
    readonly synonymous: EnrichmentEffectResult,
    readonly childrenStats: ChildrenStats
  ) { }

}

export class EnrichmentResults {
  static fromJson(json: any): EnrichmentResults {
    return new EnrichmentResults(
      json['desc'],
      EnrichmentResult.fromJsonArray(json['result'])
    );
  }

  constructor(
    readonly description: string,
    readonly results: Array<EnrichmentResult>
  ) { }

}
