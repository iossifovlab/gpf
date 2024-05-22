import { AfterContentChecked, ChangeDetectorRef, Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
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
export class DatasetNodeComponent implements OnInit, AfterContentChecked {
  @Input() public datasetNode: DatasetNode;
  @Output() public setExpandabilityEvent = new EventEmitter<boolean>();
  public selectedDataset$: Observable<Dataset>;
  public isExpanded = false;

  public constructor(
    private router: Router,
    private datasetsService: DatasetsService,
    private changeDetector: ChangeDetectorRef,
  ) { }

  public ngOnInit(): void {
    this.selectedDataset$ = this.datasetsService.getSelectedDatasetObservable();
    this.selectedDataset$.subscribe(dataset => {
      if (dataset.id === 'ALL_genotypes' && this.datasetNode.dataset.id === 'ALL_genotypes') {
        this.isExpanded = true;
      } else if (this.datasetNode.dataset.id === dataset.id) {
        this.setExpandability();
      }
    });
  }

  public ngAfterContentChecked(): void {
    this.changeDetector.detectChanges();
  }

  public setExpandability(): void {
    this.setExpandabilityEvent.emit(true);
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

  public setIsExpanded(): void {
    this.isExpanded = true;
    this.setExpandability();
  }

  public toggleDatasetCollapse(): void {
    this.isExpanded = !this.isExpanded;
  }
}
