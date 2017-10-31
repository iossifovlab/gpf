export class GeneWeights {
  readonly logScaleY: boolean;
  static fromJson(json: any): GeneWeights {
    return new GeneWeights(
      json['bars'],
      json['weight'],
      json['bins'],
      json['desc'],
      json['yscale']
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<GeneWeights> {
    return jsonArray.map((json) => GeneWeights.fromJson(json));
  }


  constructor(
    readonly bars: number[],
    readonly weight: string,
    readonly bins: number[],
    readonly desc: string,
    yScale: string
  ) { 
    if (yScale == 'log') {
      this.logScaleY = true;
    }
    else {
      this.logScaleY = false;
    }

  }

}

export class Partitions {
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

  constructor(
    readonly leftCount: number,
    readonly leftPercent: number,
    readonly midCount: number,
    readonly midPercent: number,
    readonly rightCount: number,
    readonly rightPercent: number,
  ) { }

}
