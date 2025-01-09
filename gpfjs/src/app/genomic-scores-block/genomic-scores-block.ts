export class GenomicScore {
  public static fromJson(json: object): GenomicScore {
    let histogram: NumberHistogram | CategoricalHistogram;
    /* eslint-disable @typescript-eslint/no-unsafe-member-access */
    /* eslint-disable @typescript-eslint/no-unsafe-assignment */
    if (json['histogram']['config']['type'] as string === 'number') {
      histogram = new NumberHistogram(
        json['histogram']['bars'] as number[],
        json['histogram']['bins'] as number[],
        json['large_values_desc'] as string,
        json['small_values_desc'] as string,
        json['histogram']['config']['view_range']['min'] as number,
        json['histogram']['config']['view_range']['max'] as number,
        json['histogram']['config']['x_log_scale'] as boolean,
        json['histogram']['config']['y_log_scale'] as boolean,
      );
    } else if (json['histogram']['config']['type'] as string === 'categorical') {
      const values: {name: string, value: number}[] = [];
      Object.keys(json['histogram']['values'] as object).forEach(key => {
        values.push({name: key, value: json['histogram']['values'][key]});
      });

      let valueOrder: string[] = [];
      if (json['histogram']['config']['value_order']?.length > 0) {
        valueOrder = json['histogram']['config']['value_order'];
      }

      histogram = new CategoricalHistogram(
        values,
        valueOrder,
        json['large_values_desc'] as string,
        json['small_values_desc'] as string,
        json['histogram']['config']['y_log_scale'] as boolean,
        json['histogram']['config']['displayed_values_count'] as number,
        json['histogram']['config']['displayed_values_percent'] as number,
      );
    }
    /* eslint-enable */

    return new GenomicScore(
      json['desc'] as string,
      json['help'] as string,
      json['score'] as string,
      histogram,
    );
  }

  public static fromJsonArray(jsonArray: Array<object>): Array<GenomicScore> {
    return jsonArray.map((json) => {
      return GenomicScore.fromJson(json);
    });
  }

  public constructor(
    public readonly desc: string,
    public readonly help: string,
    public readonly score: string,
    public readonly histogram: NumberHistogram | CategoricalHistogram,
  ) {

  }
}

export class NumberHistogram {
  public constructor(
    public readonly bars: number[],
    public readonly bins: number[],
    public readonly largeValuesDesc: string,
    public readonly smallValuesDesc: string,
    public readonly rangeMin: number,
    public readonly rangeMax: number,
    public readonly logScaleX: boolean,
    public readonly logScaleY: boolean,
  ) {
    if (bins.length === (bars.length + 1)) {
      bars.push(0);
    }
  }
}

export class CategoricalHistogram {
  public constructor(
    public readonly values: {name: string, value: number}[],
    public readonly valueOrder: string[],
    public readonly largeValuesDesc: string,
    public readonly smallValuesDesc: string,
    public readonly logScaleY: boolean,
    public readonly displayedValuesCount: number = null,
    public readonly displayedValuesPercent: number = null,
  ) {
    values.sort((a, b) => {
      return valueOrder.indexOf(a.name) - valueOrder.indexOf(b.name);
    });

    let maxShown = values.length;
    if (displayedValuesCount) {
      maxShown = displayedValuesCount;
    } else if (displayedValuesPercent) {
      maxShown = Math.floor(values.length / 100 * displayedValuesPercent);
    } else {
      maxShown = 100;
    }

    const otherSum = values
      .splice(maxShown, values.length)
      .reduce((acc, v) => acc + v.value, 0);
    if (otherSum !== 0) {
      values.push({name: 'other', value: otherSum});
    }
  }
}

export type CategoricalHistogramView = 'range selector' | 'click selector';

