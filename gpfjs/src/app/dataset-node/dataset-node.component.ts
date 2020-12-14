import { Component, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Observable } from 'rxjs/internal/Observable';
import { DatasetNode } from './dataset-node';

@Component({
  selector: 'gpf-dataset-node',
  templateUrl: './dataset-node.component.html',
  styleUrls: ['./dataset-node.component.css']
})
export class DatasetNodeComponent implements OnInit {
  @Input() datasetNode: DatasetNode;
  selectedDataset$: Observable<Dataset>;

  constructor(
    private router: Router,
    private datasetsService: DatasetsService,
  ) { }

  ngOnInit(): void {
    this.selectedDataset$ = this.datasetsService.getSelectedDataset();
  }

  select() {
    if (this.datasetNode !== undefined && this.datasetNode.dataset !== undefined) {
      this.router.navigate(['/', 'datasets', this.datasetNode.dataset.id, this.findFirstTool(this.datasetNode.dataset)]);
    }
  }

  findFirstTool(selectedDataset: Dataset) {
    if (selectedDataset.description) {
      return 'description';
    } else if (selectedDataset.commonReport['enabled']) {
      return 'commonReport';
    } else if (selectedDataset.genotypeBrowser && selectedDataset.genotypeBrowserConfig) {
      return 'browser';
    } else if (selectedDataset.phenotypeBrowser) {
      return 'phenotypeBrowser';
    } else if (selectedDataset.enrichmentTool) {
      return 'enrichment';
    } else if (selectedDataset.phenotypeTool) {
      return 'phenoTool';
    } else {
      return '';
    }
  }
}
