export class GeneSetsCollection {

  constructor(
      readonly name: string,
      readonly desc: string,
      readonly types: Array<any>
  ) {}

  static fromJson(json: any): GeneSetsCollection {
    return new GeneSetsCollection(
      json['name'],
      json['desc'],
      json['types']
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<GeneSetsCollection> {
    return jsonArray.map((json) => GeneSetsCollection.fromJson(json));
  }
}

export class GeneSet {

  constructor(
      readonly name: string,
      readonly count: number,
      readonly desc: string
  ) {}

  static fromJson(json: any): GeneSet {
    return new GeneSet(
      json['name'],
      +json['count'],
      json['desc']
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<GeneSet> {
    return jsonArray.map((json) => GeneSet.fromJson(json));
  }
}
