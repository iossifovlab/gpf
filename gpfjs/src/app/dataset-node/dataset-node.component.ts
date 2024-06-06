import { AfterContentChecked, ChangeDetectorRef, Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { Router } from '@angular/router';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Observable, Subject, Subscription } from 'rxjs';
import { DatasetNode } from './dataset-node';
import { Store } from '@ngxs/store';
import { StatefulComponent } from 'app/common/stateful-component';
import { DatasetNodeModel, DatasetNodeState, SetExpandedDatasets } from './dataset-node.state';

@Component({
  selector: 'gpf-dataset-node',
  templateUrl: './dataset-node.component.html',
  styleUrls: ['./dataset-node.component.css']
})
export class DatasetNodeComponent extends StatefulComponent implements OnInit, AfterContentChecked {
  @Input() public datasetNode: DatasetNode;
  @Output() public setExpandabilityEvent = new EventEmitter<boolean>();
  public selectedDataset$: Observable<Dataset>;
  public isExpanded = false;
  public closeChildrenSubject: Subject<void> = new Subject<void>();
  @Input() public closeObservable: Observable<void> = new Observable<void>();
  public closeChildrenSubscription: Subscription;

  public constructor(
    private router: Router,
    private datasetsService: DatasetsService,
    private changeDetector: ChangeDetectorRef,
    protected store: Store
  ) {
    super(store, DatasetNodeState, 'datasetNode');
  }

  public ngOnInit(): void {
    this.selectedDataset$ = this.datasetsService.getSelectedDatasetObservable();
    this.selectedDataset$.subscribe(dataset => {
      if (this.datasetNode.dataset.id === dataset.id) {
        this.setExpandability();
      }
    });

    this.store.selectOnce(
      (state: { datasetNodeState: DatasetNodeModel}) => state.datasetNodeState)
      .subscribe(state => {
        if (state.expandedDatasets.has(this.datasetNode.dataset.id)) {
          this.isExpanded = true;
        }
      });

    this.closeChildrenSubscription = this.closeObservable.subscribe(() => {
      this.isExpanded = false;
      this.removeFromState(this.datasetNode.dataset.id);
      this.emitEventToChild();
    });
  }

  public ngAfterContentChecked(): void {
    this.changeDetector.detectChanges();
  }

  public setExpandability(): void {
    this.setExpandabilityEvent.emit(true);
  }

  public emitEventToChild(): void {
    this.closeChildrenSubject.next();
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

  private addToState(nodeId: string): void {
    this.store.selectOnce(
      (state: { datasetNodeState: DatasetNodeModel}) => state.datasetNodeState)
      .subscribe(state => {
        state.expandedDatasets.add(nodeId);
        this.store.dispatch(new SetExpandedDatasets(state.expandedDatasets));
      });
  }

  private removeFromState(nodeId: string): void {
    this.store.selectOnce(
      (state: { datasetNodeState: DatasetNodeModel}) => state.datasetNodeState)
      .subscribe(state => {
        state.expandedDatasets.delete(nodeId);
        this.store.dispatch(new SetExpandedDatasets(state.expandedDatasets));
      });
  }

  private updateState(nodeId: string): void {
    this.store.selectOnce(
      (state: { datasetNodeState: DatasetNodeModel}) => state.datasetNodeState)
      .subscribe(state => {
        if (state.expandedDatasets.has(nodeId)) {
          state.expandedDatasets.delete(nodeId);
        } else {
          state.expandedDatasets.add(nodeId);
        }
        this.store.dispatch(new SetExpandedDatasets(state.expandedDatasets));
      });
  }

  public setIsExpanded(): void {
    this.isExpanded = true;
    this.addToState(this.datasetNode.dataset.id);
    this.setExpandability();
  }

  public toggleDatasetCollapse(selectedNodeId: string): void {
    this.updateState(selectedNodeId);
    this.isExpanded = !this.isExpanded;
    if (!this.isExpanded) {
      this.emitEventToChild();
    }
  }
}
