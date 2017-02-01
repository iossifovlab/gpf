export class GeneWeights {

  constructor(
      readonly bars: number[],
      readonly weight: string,
      readonly min: number,
      readonly max: number,
      readonly step: number,
      readonly bins: number[],
      readonly desc: string,
  ) {}

  static fromJson(json: any): GeneWeights {
    return new GeneWeights(
      json['bars'],
      json['weight'],
      +json['min'],
      +json['max'],
      +json['step'],
      json['bins'],
      json['desc']
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<GeneWeights> {
    return jsonArray.map((json) => GeneWeights.fromJson(json));
  }
}
