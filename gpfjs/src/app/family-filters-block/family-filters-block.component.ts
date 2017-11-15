import { Component, AfterViewInit, Input, forwardRef, ViewChild,
         ChangeDetectorRef, OnDestroy } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';
import { PHENO_FILTERS_RESET } from '../pheno-filters/pheno-filters';
import { FAMILY_IDS_RESET } from '../family-ids/family-ids';

import { Store } from '@ngrx/store';
import { Subject } from 'rxjs/Subject';
import { NgbTabChangeEvent } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-family-filters-block',
  templateUrl: './family-filters-block.component.html',
  styleUrls: ['./family-filters-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => FamilyFiltersBlockComponent) }]
})
export class FamilyFiltersBlockComponent extends QueryStateCollector implements AfterViewInit, OnDestroy {
  @Input() dataset: Dataset;
  @Input() genotypeBrowserState: Object;
  @ViewChild('tabset') ngbTabset;

  private ngUnsubscribe: Subject<void> = new Subject<void>();

  constructor(
    private store: Store<any>,
    private stateRestoreService: StateRestoreService,
    private changeDetectorRef: ChangeDetectorRef
  ) {
    super();
  }


  ngAfterViewInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .takeUntil(this.ngUnsubscribe)
      .subscribe(
        (state) => {
          if ('familyIds' in state) {
            this.ngbTabset.select('family-ids');
          } else if ('phenoFilters' in state) {
            this.ngbTabset.select('pheno-filters');
          }

          this.changeDetectorRef.detectChanges();
        }
      );
  }

  ngOnDestroy() {
    this.ngUnsubscribe.next();
    this.ngUnsubscribe.complete();
  }

  resetFiltersIfAllFamilies(event: NgbTabChangeEvent) {
    if (event.activeId && event.nextId === 'all-families') {
        this.store.dispatch({
          'type': FAMILY_IDS_RESET
        });
        this.store.dispatch({
          'type': PHENO_FILTERS_RESET
        });
    }
  }

}
