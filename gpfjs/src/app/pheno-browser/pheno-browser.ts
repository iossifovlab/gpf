import { environment } from '../../environments/environment';

export type PhenoInstrument = string;

export class PhenoInstruments {
  readonly default: PhenoInstrument;
  constructor(
    default_: PhenoInstrument, // `readonly default: string` makes TypeScript upset :(
    readonly instruments: Array<PhenoInstrument>
  ) {
    this.default = default_;
  }
}

export type ValuesDomain = [number, number];

export class PhenoMeasure {
  constructor(
    readonly index: number,
    readonly instrumentName: string,
    readonly valuesDomain: ValuesDomain,

    readonly figureDistribution: string,
    readonly figureDistributionSmall: string,

    readonly figureCorrelationNviq: string,
    readonly figureCorrelationNviqSmall: string,
    readonly pvalueCorrelationNviqMale: number,
    readonly pvalueCorrelationNviqFemale: number,

    readonly figureCorrelationAge: string,
    readonly figureCorrelationAgeSmall: string,
    readonly pvalueCorrelationAgeMale: number,
    readonly pvalueCorrelationAgeFemale: number,

    readonly measureId: string,
    readonly measureName: string,
    readonly measureType: string,
  ) { }

  static fromJson(json: Object): PhenoMeasure {
    return new PhenoMeasure(
      json['Index'] as number,
      json['instrument_name'],
      JSON.parse(json['values_domain']) as ValuesDomain,

      json['figure_distribution'],
      json['figure_distribution_small'],

      json['figure_correlation_nviq'],
      json['figure_correlation_nviq_small'],
      json['pvalue_correlation_nviq_male'] as number,
      json['pvalue_correlation_nviq_female'] as number,

      json['figure_correlation_age'],
      json['figure_correlation_age_small'],
      json['pvalue_correlation_age_male'] as number,
      json['pvalue_correlation_age_female'] as number,

      json['measure_id'],
      json['measure_name'],
      json['measure_type'],
    );
  }
}

export class PhenoMeasures {
  constructor(
    readonly baseImageUrl: string,
    readonly measures: Array<PhenoMeasure>
  ) {}

  static fromJson(json: Object): PhenoMeasures {
    return new PhenoMeasures(
      json['base_image_url'],
      json['measures'].map((phenoMeasure) => PhenoMeasure.fromJson(phenoMeasure)));
  }

  static addBasePath(phenoMeasures: PhenoMeasures): PhenoMeasures {
    return new PhenoMeasures(
      phenoMeasures.baseImageUrl,
      phenoMeasures.measures.map(phenoMeasure => new PhenoMeasure(
        phenoMeasure.index,
        phenoMeasure.instrumentName,
        phenoMeasure.valuesDomain,

        environment.basePath + phenoMeasures.baseImageUrl + phenoMeasure.figureDistribution,
        environment.basePath + phenoMeasures.baseImageUrl + phenoMeasure.figureDistributionSmall,

        environment.basePath + phenoMeasures.baseImageUrl + phenoMeasure.figureCorrelationNviq,
        environment.basePath + phenoMeasures.baseImageUrl + phenoMeasure.figureCorrelationNviqSmall,
        phenoMeasure.pvalueCorrelationNviqMale,
        phenoMeasure.pvalueCorrelationNviqFemale,

        environment.basePath + phenoMeasures.baseImageUrl + phenoMeasure.figureCorrelationAge,
        environment.basePath + phenoMeasures.baseImageUrl + phenoMeasure.figureCorrelationAgeSmall,
        phenoMeasure.pvalueCorrelationAgeMale,
        phenoMeasure.pvalueCorrelationAgeFemale,

        phenoMeasure.measureId,
        phenoMeasure.measureName,
        phenoMeasure.measureType,
      ))
    )
  }
}
