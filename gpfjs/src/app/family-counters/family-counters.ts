export class FamilyCount {
    constructor(
        readonly all: number,
        readonly male: number,
        readonly female: number,
    ) {}

    static fromJson(json: any): FamilyCount {
      return new FamilyCount(
        json['all'],
        json['M'],
        json['F']
      );
    }
}

export class FamilyObject {
    constructor(
        readonly count: FamilyCount,
        readonly color: string,
        readonly name: string
    ) {}

    static fromJson(json: any): FamilyObject {
        return new FamilyObject(
            FamilyCount.fromJson(json['count']),
            json['color'],
            json['name']
        )
    }

}

export class FamilyObjectArray {
  constructor(
    readonly objects: Array<FamilyObject>
  ) {}

  static fromJsonArray(json: Array<Object>): FamilyObjectArray {
    return new FamilyObjectArray(
        json.map(familyObject => FamilyObject.fromJson(familyObject))
    );
  }
}
