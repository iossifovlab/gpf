import { AfterContentChecked, ChangeDetectorRef, Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, Subject, Subscription, take } from 'rxjs';
import { DatasetNode } from './dataset-node';
import { Store } from '@ngrx/store';
import { selectExpandedDatasets, setExpandedDatasets } from './dataset-node.state';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { ComponentValidator } from 'app/common/component-validator';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-dataset-node',
  templateUrl: './dataset-node.component.html',
  styleUrls: ['./dataset-node.component.css'],
  standalone: false
})
export class DatasetNodeComponent extends ComponentValidator implements OnInit, AfterContentChecked {
  @Input() public datasetNode: DatasetNode;
  @Output() public setExpandabilityEvent = new EventEmitter<boolean>();
  public selectedDatasetId: string;
  public isExpanded = false;
  public closeChildrenSubject: Subject<void> = new Subject<void>();
  @Input() public closeObservable: Observable<void> = new Observable<void>();
  public closeChildrenSubscription: Subscription;

  public constructor(
    private router: Router,
    private changeDetector: ChangeDetectorRef,
    protected store: Store
  ) {
    super(store, 'datasetNode', selectExpandedDatasets);
  }

  public ngOnInit(): void {
    this.store.select(selectDatasetId).pipe(take(1)).subscribe(datasetId => {
      this.selectedDatasetId = datasetId;
      if (this.datasetNode.dataset.id === this.selectedDatasetId) {
        this.setExpandability();
      }
    });

    this.store.select(selectExpandedDatasets).pipe(take(1)).subscribe((expandedDatasets: string[]) => {
      if (expandedDatasets.includes(this.datasetNode.dataset.id)) {
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
    if (!this.datasetNode?.dataset) {
      return;
    }

    const url = `/datasets/${this.datasetNode.dataset.id}`;

    if (openInNewTab) {
      const newWindow = window.open('', '_blank');
      if (newWindow) {
        newWindow.location.assign(url);
      }
    } else {
      if (this.datasetNode.dataset.id === this.selectedDatasetId) {
        return;
      }
      this.router.navigate([url]);
    }
  }

  private addToState(nodeId: string): void {
    this.store.select(selectExpandedDatasets).pipe(take(1)).subscribe((expandedDatasetsState: string[]) => {
      const expandedDatasets = cloneDeep(expandedDatasetsState);
      if (!expandedDatasets.includes(nodeId)) {
        expandedDatasets.push(nodeId);
        this.store.dispatch(setExpandedDatasets({expandedDatasets: expandedDatasets}));
      }
    });
  }

  private removeFromState(nodeId: string): void {
    this.store.select(selectExpandedDatasets).pipe(take(1)).subscribe((expandedDatasetsState: string[]) => {
      const expandedDatasets = cloneDeep(expandedDatasetsState);
      if (expandedDatasets.includes(nodeId)) {
        const index = expandedDatasets.indexOf(nodeId, 0);
        expandedDatasets.splice(index, 1);
        this.store.dispatch(setExpandedDatasets({expandedDatasets: expandedDatasets}));
      }
    });
  }

  private updateState(nodeId: string): void {
    this.store.select(selectExpandedDatasets).pipe(take(1)).subscribe((expandedDatasetsState: string[]) => {
      const expandedDatasets = cloneDeep(expandedDatasetsState);
      if (expandedDatasets.includes(nodeId)) {
        const index = expandedDatasets.indexOf(nodeId, 0);
        expandedDatasets.splice(index, 1);
      } else {
        expandedDatasets.push(nodeId);
      }
      this.store.dispatch(setExpandedDatasets({expandedDatasets: expandedDatasets}));
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
