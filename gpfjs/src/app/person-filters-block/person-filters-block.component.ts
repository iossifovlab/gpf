import { Component, AfterViewInit, Input, forwardRef, ViewChild, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';


@Component({
  selector: 'gpf-person-filters-block',
  templateUrl: './person-filters-block.component.html',
  styleUrls: ['./person-filters-block.component.css'],
  providers: [{
    provide: QueryStateCollector,
    useExisting: forwardRef(() => PersonFiltersBlockComponent)
  }]
})
export class PersonFiltersBlockComponent extends QueryStateCollector implements OnInit, AfterViewInit {
  @Input() dataset: Dataset;
  @Input() genotypeBrowserState: Object;
  @ViewChild('nav') ngbNav;
  showAdvancedButton: boolean;

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit(): void {
    this.showAdvancedButton = this.dataset.genotypeBrowserConfig.personFilters.length !== 0;
  }

  ngAfterViewInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
          if ('personIds' in state) {
            this.ngbNav.select('personIds');
          } else if ('personFilters' in state) {
            this.ngbNav.select('advanced');
          }
        }
      );
  }
}
