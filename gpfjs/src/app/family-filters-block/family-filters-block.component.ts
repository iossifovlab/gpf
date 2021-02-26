import { Component, AfterViewInit, Input, forwardRef, ViewChild, OnInit } from '@angular/core';
import { DatasetsService } from 'app/datasets/datasets.service';
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
export class FamilyFiltersBlockComponent extends QueryStateCollector implements OnInit, AfterViewInit {
  @Input() dataset: Dataset;
  @Input() genotypeBrowserState: Object;
  @ViewChild('nav') ngbNav;
  showFamilyTypeFilter: boolean;
  showAdvancedButton: boolean;

  constructor(
    private stateRestoreService: StateRestoreService,
    private datasetsService: DatasetsService,
  ) {
    super();
  }

  ngOnInit(): void {
    this.showFamilyTypeFilter = this.dataset.genotypeBrowserConfig.hasFamilyStructureFilter;
    this.showAdvancedButton =
      this.dataset.genotypeBrowserConfig.familyFilters.length !== 0 ||
      this.dataset.genotypeBrowserConfig.hasFamilyStructureFilter;
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
}
