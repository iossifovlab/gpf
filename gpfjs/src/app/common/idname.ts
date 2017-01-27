export class IdName {
  static asIdName(json: any): IdName {
    return new IdName(json['id'], json['name']);
  }

  static asIdNameArray(jsonArray: Array<Object>): Array<IdName> {
    return jsonArray.map((json) => IdName.asIdName(json));
  }

  constructor(
    readonly id: string,
    readonly name: string
  ) { }

}
