import { environment } from '../../environments/environment';

function addBaseUrlIfNotNull(currentPath: string, bp: string): string {
  if (currentPath) {
    return bp + currentPath;
  }
  return null;
}

export class PhenoRegression {
  public regressionId: string;
  public measureId: string;
  public figureRegression: string;
  public figureRegressionSmall: string;
  public pvalueRegressionMale: number;
  public pvalueRegressionFemale: number;

  public constructor(json: object) {
    this.regressionId = json['regression_id'] as string;
    this.measureId = json['measure_id'] as string;
    this.figureRegression = json['figure_regression'] as string;
    this.figureRegressionSmall = json['figure_regression_small'] as string;
    this.pvalueRegressionMale = json['pvalue_regression_male'] as number;
    this.pvalueRegressionFemale = json['pvalue_regression_female'] as number;
  }

  public addBasePath(basePath: string): void {
    this.figureRegression = addBaseUrlIfNotNull(this.figureRegression, basePath);
    this.figureRegressionSmall = addBaseUrlIfNotNull(this.figureRegressionSmall, basePath);
  }
}

export class PhenoRegressions {
  public static emptyRegression = new PhenoRegression({
    /* eslint-disable @typescript-eslint/naming-convention */
    figure_regression: null,
    figure_regression_small: null,
    pvalue_regression_male: null,
    pvalue_regression_female: null
    /* eslint-enable */
  });

  public constructor(regArr: object[]) {
    regArr.forEach(reg => {
      this[reg['regression_id']] = new PhenoRegression(reg);
    });
  }

  public addBasePath(basePath: string): void {
    for (const reg of Object.getOwnPropertyNames(this)) {
      this[reg].addBasePath(basePath);
    }
  }

  public getReg(name: string): PhenoRegression {
    if (this.hasOwnProperty(name)) {
      return this[name];
    } else {
      return PhenoRegressions.emptyRegression;
    }
  }
}

export type PhenoInstrument = string;

export class PhenoInstruments {
  public readonly default: PhenoInstrument;
  public constructor(
    default_: PhenoInstrument, // `readonly default: string` makes TypeScript upset :(
    public readonly instruments: Array<PhenoInstrument>
  ) {
    this.default = default_;
  }
}

export class PhenoMeasure {
  public static fromJson(json: object): PhenoMeasure {
    return new PhenoMeasure(
      json['Index'] as number,
      json['instrument_name'] as string,
      json['values_domain'] as string,

      json['figure_distribution'] as string,
      json['figure_distribution_small'] as string,

      json['measure_id'] as string,
      json['measure_name'] as string,
      json['measure_type'] as string,
      json['description'] as string,

      new PhenoRegressions(json['regressions'] as object[]),

      json['base_url'] as string
    );
  }

  public static addBasePath(measure: PhenoMeasure, basePath: string): PhenoMeasure {
    basePath = `${environment.basePath}/${basePath}`;
    const newMeasure: PhenoMeasure = new PhenoMeasure(
      measure.index,
      measure.instrumentName,
      measure.valuesDomain,

      addBaseUrlIfNotNull(measure.figureDistribution, basePath),
      addBaseUrlIfNotNull(measure.figureDistributionSmall, basePath),

      measure.measureId,
      measure.measureName,
      measure.measureType,
      measure.description,

      measure.regressions,

      measure.baseUrl
    );
    return newMeasure;
  }

  public constructor(
    public readonly index: number,
    public readonly instrumentName: string,
    public readonly valuesDomain: string,

    public readonly figureDistribution: string,
    public readonly figureDistributionSmall: string,

    public readonly measureId: string,
    public readonly measureName: string,
    public readonly measureType: string,
    public readonly description: string,

    public readonly regressions: PhenoRegressions,

    public readonly baseUrl: string,
  ) { }
}

export class PhenoMeasures {
  public addMeasure(measure: PhenoMeasure): void {
    let basePath: string;
    if (measure.baseUrl) {
      basePath = measure.baseUrl + this.baseImageUrl;
    } else {
      basePath = environment.basePath + '/' + this.baseImageUrl;
    }

    measure.regressions.addBasePath(basePath);

    const newMeasure: PhenoMeasure = new PhenoMeasure(
      measure.index,
      measure.instrumentName,
      measure.valuesDomain,

      addBaseUrlIfNotNull(measure.figureDistribution, basePath),
      addBaseUrlIfNotNull(measure.figureDistributionSmall, basePath),

      measure.measureId,
      measure.measureName,
      measure.measureType,
      measure.description,

      measure.regressions,

      measure.baseUrl
    );
    this.measures.push(newMeasure);
  }

  public static fromJson(json: object): PhenoMeasures {
    const measures = new PhenoMeasures(
      json['base_image_url'] as string,
      [],
      json['has_descriptions'] as boolean,
      json['regression_names'] as object);
    if (json['measures']) {
      for (const measure of json['measures']) {
        const m = PhenoMeasure.fromJson(measure as object);
        measures.addMeasure(m);
      }
    }
    return measures;
  }

  public constructor(
    public readonly baseImageUrl: string,
    public readonly measures: Array<PhenoMeasure>,
    public readonly hasDescriptions: boolean,
    public readonly regressionNames: object
  ) { }
}
