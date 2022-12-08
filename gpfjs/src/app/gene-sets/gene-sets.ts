export class GeneSetsCollection {
  public static fromJson(json: any): GeneSetsCollection {
    return new GeneSetsCollection(
      json['name'],
      json['desc'],
      GeneSetType.fromJsonArray(json['types'])
    );
  }

  public static fromJsonArray(jsonArray: Array<Object>): Array<GeneSetsCollection> {
    return jsonArray.map((json) => GeneSetsCollection.fromJson(json));
  }

  public constructor(
    public readonly name: string,
    public readonly desc: string,
    public readonly types: Array<GeneSetType>,
  ) { }
}

export class GeneSet {
  public static fromJson(json: object): GeneSet {
    return new GeneSet(
      json['name'],
      +json['count'],
      json['desc'],
      json['download']
    );
  }

  public static fromJsonArray(jsonArray: Array<object>): Array<GeneSet> {
    return jsonArray.map((json) => GeneSet.fromJson(json));
  }

  public constructor(
    public readonly name: string,
    public readonly count: number,
    public readonly desc: string,
    public readonly download: string,
  ) { }
}

export class GeneSetType {
  public static fromJsonArray(jsonArray: Array<GeneSetType>): Array<GeneSetType> {
    const result: Array<GeneSetType> = [];
    for (const geneSetType of jsonArray) {
      result.push(GeneSetType.fromJson(geneSetType));
    }
    return result;
  }

  public static fromJson(json: GeneSetType): GeneSetType {
    return new GeneSetType(
      json.datasetId, json.datasetName, json.personSetCollectionId,
      json.personSetCollectionName, json.personSetCollectionLegend
    );
  }

  public constructor(
    public readonly datasetId: string,
    public readonly datasetName: string,
    public readonly personSetCollectionId: string,
    public readonly personSetCollectionName: string,
    public readonly personSetCollectionLegend: Array<any>
  ) { }
}
