import { Component, AfterViewInit, Input, forwardRef, ViewChild } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

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
  @ViewChild('nav') ngbNav;

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngAfterViewInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {

          if ('familyIds' in state) {
            this.ngbNav.select('familyIds');
          } else if ('personFilters' in state) {
            this.ngbNav.select('advanced');
          }

        }
      );
  }

  ngOnDestroy() {
  }

}
