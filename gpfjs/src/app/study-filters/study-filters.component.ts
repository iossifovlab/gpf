import { Component, OnInit, Input, ViewChild, OnDestroy } from '@angular/core';
import { Store } from '@ngxs/store';
import { Dataset } from '../datasets/datasets';
import { SetStudyFilters, StudyFiltersModel, StudyFiltersState } from './study-filters.state';
import { StatefulComponent } from 'app/common/stateful-component';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { StateReset } from 'ngxs-reset-plugin';
import { SetNotEmpty } from 'app/utils/set.validators';
import { Validate } from 'class-validator';
import { DatasetNode } from 'app/dataset-node/dataset-node';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Subscription } from 'rxjs/internal/Subscription';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';

@Component({
  selector: 'gpf-study-filters-block',
  templateUrl: './study-filters.component.html',
  styleUrls: ['./study-filters.component.css']
})
export class StudyFiltersComponent extends StatefulComponent implements OnInit, OnDestroy {
  @Input() public dataset: Dataset;

  @Validate(SetNotEmpty, {message: 'Select at least one.'})
  public selectedStudies: Set<string> = new Set<string>(['']); // Used by the child component(Treelist checkbox)
  public rootDataset: DatasetNode = null;
  public datasetSubscription: Subscription;

  @ViewChild('nav') public ngbNav: NgbNav;

  public constructor(
    protected store: Store, public datasets: DatasetsService, private datasetsTreeService: DatasetsTreeService
  ) {
    super(store, StudyFiltersState, 'studyFilters');
  }

  public showStudyFilters = false;

  public ngOnInit(): void {
    super.ngOnInit();
    const datasets$ = this.datasets.getDatasetsObservable();
    const datasetTrees = new Array<DatasetNode>();
    this.datasetSubscription = datasets$.subscribe(datasets => {
      datasets.filter(d => !d.parents.length).map(d => {
        datasetTrees.push(new DatasetNode(d, datasets));
      });
      for (const tree of datasetTrees) {
        const node = this.datasetsTreeService.findNodeById(tree, this.dataset.id);
        if (node) {
          this.rootDataset = node;
          break;
        }
      }
    });
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    this.store.selectOnce(state => state.studyFiltersState as StudyFiltersModel).subscribe(state => {
      // restore state
      if ((state?.studyFilters?.length ?? 0) !== 0) {
        setTimeout(() => {
          if (this.showStudyFilters === false) {
            this.showStudyFilters = true;
            this.ngbNav.select('studies');
            this.updateState(new Set(state.studyFilters));
          }
        }, 200);
      }
    });
  }

  public ngOnDestroy(): void {
    this.datasetSubscription.unsubscribe();
  }

  public onNavChange(): void {
    if (this.ngbNav.activeId === 'studies') {
      // The line below adds empty string to selected studies, otherwise the selected studies
      // are going to be empty, which prevents the proper validation for selectedStudies
      this.selectedStudies.add('');
    } else {
      this.selectedStudies.clear();
    }
    this.store.dispatch(new SetStudyFilters([]));
    this.store.dispatch(new StateReset(StudyFiltersState));
  }

  public updateState(newValues: Set<string>): void {
    this.selectedStudies = newValues;
    this.store.dispatch(new SetStudyFilters(Array.from(this.selectedStudies)));
  }
}
