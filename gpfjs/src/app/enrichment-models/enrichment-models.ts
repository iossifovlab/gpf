import { IdDescription } from '../common/iddescription';


export class EnrichmentModels {
  static fromJson(json: any): EnrichmentModels {
    if (!json) {
      return undefined;
    }

    return new EnrichmentModels(
      json['counting'].map((json) => new IdDescription(json.name, json.desc)),
      json['background'].map((json) => new IdDescription(json.name, json.desc)),
    );
  }

  constructor(
    readonly countings: Array<IdDescription>,
    readonly backgrounds: Array<IdDescription>
  ) {
  }
}
