import { environment } from '../../environments/environment';

function addBaseUrlIfNotNull(currentPath: string, bp: string): string {
  if (currentPath) {
    return bp + currentPath;
  }
  return null;
};

export class PhenoRegression {

  regressionName: string;
  measureId: string;
  regressionMeasureId: string;
  figureRegression: string;
  figureRegressionSmall: string;
  pvalueRegressionMale: number;
  pvalueRegressionFemale: number;

  constructor(json: Object) {
    this.regressionName = json['regression_name'];
    this.measureId = json['measure_id'];
    this.regressionMeasureId = json['regression_measure_id'];
    this.figureRegression = json['figure_regression'];
    this.figureRegressionSmall = json['figure_regression_small'];
    this.pvalueRegressionMale = json['pvalue_regression_male'];
    this.pvalueRegressionFemale = json['pvalue_regression_female'];
  }

  addBasePath(basePath: string) {
    this.figureRegression = addBaseUrlIfNotNull(this.figureRegression, basePath);
    this.figureRegressionSmall = addBaseUrlIfNotNull(this.figureRegressionSmall, basePath);
  }
}

export class PhenoRegressions {

  static emptyRegression = new PhenoRegression({
    'figure_regression': null,
    'figure_regression_small': null,
    'pvalue_regression_male': null,
    'pvalue_regression_female': null
  });

  constructor(regArr: Object[]) {
    for (let i = 0; i < regArr.length; i++) {
      this[regArr[i]['regression_name']] = new PhenoRegression(regArr[i]);
    }
  }

  addBasePath(basePath: string) {
    for (let reg of Object.getOwnPropertyNames(this)) {
      this[reg].addBasePath(basePath);
    }
  }

  getReg(name: string) {
    if (this.hasOwnProperty(name)) {
      return this[name];
    } else {
      return PhenoRegressions.emptyRegression;
    }
  }
}

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

export class PhenoMeasure {

  static fromJson(json: Object): PhenoMeasure {
    return new PhenoMeasure(
      json['Index'] as number,
      json['instrument_name'],
      json['values_domain'],

      json['figure_distribution'],
      json['figure_distribution_small'],

      json['measure_id'],
      json['measure_name'],
      json['measure_type'],
      json['description'],

      new PhenoRegressions(json['regressions'])
    );
  }

  constructor(
    readonly index: number,
    readonly instrumentName: string,
    readonly valuesDomain: string,

    readonly figureDistribution: string,
    readonly figureDistributionSmall: string,

    readonly measureId: string,
    readonly measureName: string,
    readonly measureType: string,
    readonly description: string,

    readonly regressions: PhenoRegressions,
  ) { }
}

export class PhenoMeasures {

  static fromJson(json: Object): PhenoMeasures {
    return new PhenoMeasures(
      json['base_image_url'],
      json['measures'].map((phenoMeasure) => PhenoMeasure.fromJson(phenoMeasure)),
      json['has_descriptions'],
      json['regression_names']);
  }

  static addBasePath(phenoMeasures: PhenoMeasures): PhenoMeasures {
    let basePath = environment.basePath + phenoMeasures.baseImageUrl;

    phenoMeasures.measures.map(measure => measure.regressions.addBasePath(basePath));

    return new PhenoMeasures(
      phenoMeasures.baseImageUrl,
      phenoMeasures.measures.map(phenoMeasure => new PhenoMeasure(
        phenoMeasure.index,
        phenoMeasure.instrumentName,
        phenoMeasure.valuesDomain,

        addBaseUrlIfNotNull(phenoMeasure.figureDistribution, basePath),
        addBaseUrlIfNotNull(phenoMeasure.figureDistributionSmall, basePath),

        phenoMeasure.measureId,
        phenoMeasure.measureName,
        phenoMeasure.measureType,
        phenoMeasure.description,

        phenoMeasure.regressions,
      )),
      phenoMeasures.hasDescriptions,
      phenoMeasures.regressionNames
    );
  }

  constructor(
    readonly baseImageUrl: string,
    readonly measures: Array<PhenoMeasure>,
    readonly hasDescriptions: boolean,
    readonly regressionNames: string
  ) {}

}
