export interface FederationJson {
  /* eslint-disable  @typescript-eslint/naming-convention */
  description: string;
  name: string;
  // eslint-enable
}

export class FederationCredential {
  public static fromJsonArray(jsonArray: FederationJson[]): FederationCredential[] {
    return jsonArray.map(credential => FederationCredential.fromJson(credential));
  }

  public static fromJson(json: FederationJson): FederationCredential {
    return new FederationCredential(
      json['description'],
      json['name']
    );
  }

  public constructor(
    public description: string,
    public name: string) {}
}


