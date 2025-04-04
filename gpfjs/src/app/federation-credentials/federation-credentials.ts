export interface FederationGetJson {
  name: string;
}

export interface FederationPostJson {
  credentials: string;
  client_secret: string;
  client_id: string;
}

export class FederationCredential {
  public constructor(public name: string) { }

  public static fromJsonArray(jsonArray: FederationGetJson[]): FederationCredential[] {
    return jsonArray.map(credential => FederationCredential.fromJson(credential));
  }

  public static fromJson(json: FederationGetJson): FederationCredential {
    return new FederationCredential(
      json['name']
    );
  }
}

