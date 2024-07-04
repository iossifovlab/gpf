import { RegionsFilterValidator } from './regions-filter.validator';
import { Validate } from 'class-validator';
import { DatasetModel } from 'app/datasets/datasets.state';
import { Store } from '@ngxs/store';
import { switchMap } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';

export class RegionsFilter {
  @Validate(RegionsFilterValidator)
  public regionsFilter = '';
  public genome = '';

  public constructor(public store: Store, private datasetsService: DatasetsService) {
    this.store.selectOnce((state: { datasetState: DatasetModel}) => state.datasetState).pipe(
      switchMap(state => this.datasetsService.getDataset(state.selectedDatasetId))
    ).subscribe(dataset => {
      this.genome = dataset.genome;
    });
  }
}

