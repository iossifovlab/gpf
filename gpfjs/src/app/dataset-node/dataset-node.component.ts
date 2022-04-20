import { Component, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Dataset, toolPageLinks } from 'app/datasets/datasets';
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
      let url: string;
      const firstTool = this.findFirstTool(this.datasetNode.dataset);

      if (firstTool) {
        url = `/datasets/${this.datasetNode.dataset.id}/${this.findFirstTool(this.datasetNode.dataset)}`;
      } else {
        url = `/datasets/${this.datasetNode.dataset.id}`;
      }

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

  public findFirstTool(selectedDataset: Dataset): string {
    if (selectedDataset.description) {
      return toolPageLinks.datasetDescription;
    } else if (selectedDataset.commonReport.enabled) {
      return toolPageLinks.datasetStatistics;
    } else if (selectedDataset.geneBrowser.enabled) {
      return toolPageLinks.geneBrowser;
    } else if (selectedDataset.genotypeBrowser && selectedDataset.genotypeBrowserConfig) {
      return toolPageLinks.genotypeBrowser;
    } else if (selectedDataset.phenotypeBrowser) {
      return toolPageLinks.phenotypeBrowser;
    } else if (selectedDataset.enrichmentTool) {
      return toolPageLinks.enrichmentTool;
    } else if (selectedDataset.phenotypeTool) {
      return toolPageLinks.phenotypeTool;
    } else {
      return '';
    }
  }
}
