export class IdName {
  static idNameFromJson(json: any): IdName {
    return new IdName(json['id'], json['name']);
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<IdName> {
    return jsonArray.map((json) => IdName.idNameFromJson(json));
  }

  constructor(
    readonly id: string,
    readonly name: string
  ) { }

}
