export interface FederationJson {
  name: string;
}

export class FederationCredential {
  public static fromJsonArray(jsonArray: FederationJson[]): FederationCredential[] {
    return jsonArray.map(credential => FederationCredential.fromJson(credential));
  }

  public static fromJson(json: FederationJson): FederationCredential {
    return new FederationCredential(
      json['name']
    );
  }

  public constructor(public name: string) {}
}


