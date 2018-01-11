import { Component, AfterViewInit, Input, forwardRef, ViewChild,
         ChangeDetectorRef } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

import { Subject } from 'rxjs/Subject';
import { NgbTabChangeEvent } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-family-filters-block',
  templateUrl: './family-filters-block.component.html',
  styleUrls: ['./family-filters-block.component.css'],
  providers: [{
    provide: QueryStateCollector,
    useExisting: forwardRef(() => FamilyFiltersBlockComponent)
  }]
})
export class FamilyFiltersBlockComponent extends QueryStateCollector implements AfterViewInit {
  @Input() dataset: Dataset;
  @Input() genotypeBrowserState: Object;
  @ViewChild('tabset') ngbTabset;


  constructor(
    private stateRestoreService: StateRestoreService,
    private changeDetectorRef: ChangeDetectorRef
  ) {
    super();
  }


  ngAfterViewInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {

          if ('familyIds' in state) {
            this.ngbTabset.select('family-ids');
          } else if ('phenoFilters' in state) {
            this.ngbTabset.select('pheno-filters');
          }

        }
      );
  }

}
