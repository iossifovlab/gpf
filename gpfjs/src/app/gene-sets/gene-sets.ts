export class GeneSetsCollection {

  static fromJson(json: any): GeneSetsCollection {
    return new GeneSetsCollection(
      json['name'],
      json['desc'],
      GeneSetType.fromJsonArray(json['types'])
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<GeneSetsCollection> {
    return jsonArray.map((json) => GeneSetsCollection.fromJson(json));
  }

  constructor(
    readonly name: string,
    readonly desc: string,
    readonly types: Array<GeneSetType>,
  ) { }

}

export class GeneSet {
  static fromJson(json: any): GeneSet {
    return new GeneSet(
      json['name'],
      +json['count'],
      json['desc'],
      json['download']
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<GeneSet> {
    return jsonArray.map((json) => GeneSet.fromJson(json));
  }

  constructor(
    readonly name: string,
    readonly count: number,
    readonly desc: string,
    readonly download: string,
  ) { }

}

export class GeneSetType {

  static fromJsonArray(jsonArray: Array<Object>): Array<GeneSetType> {
    const result: Array<GeneSetType> = [];
    for (const geneSetType of jsonArray) {
      result.push(GeneSetType.fromJson(geneSetType));
    }
    return result;
  }

  static fromJson(json: any): GeneSetType {
    return new GeneSetType(
      json.datasetId, json.datasetName, json.peopleGroupId,
      json.peopleGroupName, json.peopleGroupLegend
    );
  }

  constructor(
    readonly datasetId: string,
    readonly datasetName: string,
    readonly peopleGroupId: string,
    readonly peopleGroupName: string,
    readonly peopleGroupLegend: Array<any>
  ) { }
}
