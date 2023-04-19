export class FederationCredential {
  public static fromJsonArray(json): FederationCredential[] {
    return json.map(credential => FederationCredential.fromJson(credential));
  }

  public static fromJson(json): FederationCredential {
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


