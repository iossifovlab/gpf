export interface FederationJson {
  /* eslint-disable  @typescript-eslint/naming-convention */
  client_id: string;
  client_secret: string;
  name: string;
  // eslint-enable
}

export class FederationCredential {
  public static fromJsonArray(jsonArray: FederationJson[]): FederationCredential[] {
    return jsonArray.map(credential => FederationCredential.fromJson(credential));
  }

  public static fromJson(json: FederationJson): FederationCredential {
    return new FederationCredential(
      json['client_id'],
      json['client_secret'],
      json['name']
    );
  }

  public constructor(
    public clientId: string,
    public clientSecret: string,
    public name: string) {}
}


