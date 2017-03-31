export class ContinuousMeasure {
  static fromJson(json: any): ContinuousMeasure {
    return new ContinuousMeasure(
      json['measure'],
      json['min'],
      json['max'],
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<ContinuousMeasure> {
    if (!jsonArray) {
      return undefined;
    }
    return jsonArray.map((json) => ContinuousMeasure.fromJson(json));
  }

  constructor(
    readonly name: string,
    readonly min: number,
    readonly max: number
  ) {}
}
