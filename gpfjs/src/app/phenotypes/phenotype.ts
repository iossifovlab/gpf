import { IdDescription } from '../common/iddescription';

export class Phenotype extends IdDescription {
  constructor(
    readonly id: string,
    readonly description: string,
    readonly color: string
  ) {
    super(id, description);
  }
}
