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

export class Partitions {

  constructor(
      readonly leftCount: number,
      readonly leftPercent: number,
      readonly midCount: number,
      readonly midPercent: number,
      readonly rightCount: number,
      readonly rightPercent: number,
  ) {}

  static fromJson(json: any): Partitions {
    return new Partitions(
      +json['left']['count'],
      +json['left']['percent'],
      +json['mid']['count'],
      +json['mid']['percent'],
      +json['right']['count'],
      +json['right']['percent'],
    );
  }
}
