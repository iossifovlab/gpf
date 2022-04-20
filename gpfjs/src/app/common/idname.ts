export class IdName {
  public static idNameFromJson(json: object): IdName {
    return new IdName(json['id'] as string, json['name'] as string);
  }

  public static fromJsonArray(jsonArray: Array<object>): Array<IdName> {
    return jsonArray.map((json) => IdName.idNameFromJson(json));
  }

  public constructor(
    public readonly id: string,
    public readonly name: string
  ) {}
}
