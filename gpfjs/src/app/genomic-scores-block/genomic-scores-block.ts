import { NumberHistogram, CategoricalHistogram } from 'app/utils/histogram-types';

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
        json['histogram']['config']['label_rotation'] as number,
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

