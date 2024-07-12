import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset } from '../datasets/datasets';
import { switchMap, take } from 'rxjs/operators';
import { Store } from '@ngxs/store';
import { DatasetModel } from 'app/datasets/datasets.state';

@Component({
  selector: 'gpf-dataset-description',
  templateUrl: './dataset-description.component.html',
  styleUrls: ['./dataset-description.component.css']
})
export class DatasetDescriptionComponent implements OnInit {
  public dataset: Dataset;

  public constructor(
    private route: ActivatedRoute,
    private datasetsService: DatasetsService,
    private store: Store
  ) { }

  public ngOnInit(): void {
    this.store.selectOnce((state: { datasetState: DatasetModel}) => state.datasetState).pipe(
      switchMap((state: DatasetModel) => this.datasetsService.getDataset(state.selectedDatasetId as string)))
      .subscribe(dataset => {
        if (!dataset) {
          return;
        }
        this.dataset = dataset;
      });
  }

  public writeDataset(markdown: string): void {
    this.datasetsService.writeDatasetDescription(this.dataset.id, markdown).pipe(take(1)).subscribe();
  }
}
