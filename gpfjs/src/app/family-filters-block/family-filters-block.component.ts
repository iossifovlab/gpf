import { Component, OnInit, Input, forwardRef, ViewChild,
         ChangeDetectorRef} from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider'
import { StateRestoreService } from '../store/state-restore.service'
import { Subject } from 'rxjs/Subject';

@Component({
  selector: 'gpf-family-filters-block',
  templateUrl: './family-filters-block.component.html',
  styleUrls: ['./family-filters-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => FamilyFiltersBlockComponent) }]
})
export class FamilyFiltersBlockComponent extends QueryStateCollector implements OnInit {
  @Input() datasetConfig: Dataset;
  @Input() genotypeBrowserState: Object;
  @ViewChild('tabset') ngbTabset;

  private ngUnsubscribe: Subject<void> = new Subject<void>();

  constructor(
    private stateRestoreService: StateRestoreService,
    private changeDetectorRef: ChangeDetectorRef
  ) {
    super();
  }

  ngOnInit() {
  }

  ngAfterViewInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .takeUntil(this.ngUnsubscribe)
      .subscribe(
        (state) => {
          if ("familyIds" in state) {
            this.ngbTabset.select("family-ids")
          }
          else if ("phenoFilters" in state) {
            this.ngbTabset.select("pheno-filters")
          }

          this.changeDetectorRef.detectChanges()
        }
      )
  }

  ngOnDestroy() {
    this.ngUnsubscribe.next();
    this.ngUnsubscribe.complete();
  }

}
