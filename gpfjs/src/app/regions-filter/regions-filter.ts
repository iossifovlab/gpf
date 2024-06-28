import { RegionsFilterValidator } from './regions-filter.validator';
import { Validate } from 'class-validator';
import { DatasetModel } from 'app/datasets/datasets.state';
import { Store } from '@ngxs/store';

export class RegionsFilter {
  @Validate(RegionsFilterValidator)
  public regionsFilter = '';
  public genome = '';

  public constructor(public store: Store) {
    this.store.selectOnce((state: { datasetState: DatasetModel}) => state.datasetState).subscribe(state => {
      this.genome = state.selectedDataset.genome;
    });
  }
}

