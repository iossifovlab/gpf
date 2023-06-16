import { RegionsFilterValidator } from './regions-filter.validator';
import { Validate } from 'class-validator';
import { DatasetsService } from 'app/datasets/datasets.service';

export class RegionsFilter {
  @Validate(RegionsFilterValidator)
  public regionsFilter = '';
  public genome = DatasetsService.genomeVersion;
}
