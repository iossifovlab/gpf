import { IdDescription } from '../common/iddescription';
import { IsNotEmpty } from 'class-validator';

export class EnrichmentModels {
  static fromJson(json: any): EnrichmentModels {
    if (!json) {
      return undefined;
    }

    return new EnrichmentModels(
      json['counting'].map((j) => new IdDescription(json.name, json.desc)),
      json['background'].map((j) => new IdDescription(json.name, json.desc)),
    );
  }

  constructor(
    readonly countings: Array<IdDescription>,
    readonly backgrounds: Array<IdDescription>
  ) {
  }
}

export class EnrichmentModel {
  @IsNotEmpty()
  background: IdDescription;

  @IsNotEmpty()
  counting: IdDescription;
};
