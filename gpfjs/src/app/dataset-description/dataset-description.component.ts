import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset } from '../datasets/datasets';
import { take } from 'rxjs/operators';
import { Store } from '@ngxs/store';
import { DatasetModel } from 'app/datasets/datasets.state';

@Component({
  selector: 'gpf-dataset-description',
  templateUrl: './dataset-description.component.html',
  styleUrls: ['./dataset-description.component.css']
})
export class DatasetDescriptionComponent implements OnInit {
  public dataset: Dataset;
  public datasetId: string;

  public constructor(
    private route: ActivatedRoute,
    private datasetsService: DatasetsService,
    private store: Store
  ) { }

  public ngOnInit(): void {
    this.store.selectOnce((state: { datasetState: DatasetModel}) => state.datasetState).subscribe(state => {
      this.dataset = state.selectedDataset;
      this.datasetId = state.selectedDataset.id;
    });
  }

  public writeDataset(markdown: string): void {
    this.datasetsService.writeDatasetDescription(this.datasetId, markdown).pipe(take(1)).subscribe();
  }
}
