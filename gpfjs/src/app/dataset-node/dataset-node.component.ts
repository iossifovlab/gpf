import { Component, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Observable } from 'rxjs';
import { DatasetNode } from './dataset-node';

@Component({
  selector: 'gpf-dataset-node',
  templateUrl: './dataset-node.component.html',
  styleUrls: ['./dataset-node.component.css']
})
export class DatasetNodeComponent implements OnInit {
  @Input() public datasetNode: DatasetNode;
  public selectedDataset$: Observable<Dataset>;

  public constructor(
    private router: Router,
    private datasetsService: DatasetsService,
  ) { }

  public ngOnInit(): void {
    this.selectedDataset$ = this.datasetsService.getSelectedDatasetObservable();
  }

  public select(openInNewTab = false): void {
    if (this.datasetNode !== undefined && this.datasetNode.dataset !== undefined) {
      const url = `/datasets/${this.datasetNode.dataset.id}`;

      if (!openInNewTab) {
        this.router.navigate([url]);
      } else {
        const newWindow = window.open('', '_blank');
        if (newWindow) {
          newWindow.location.assign(url);
        }
      }
    }
  }
}
