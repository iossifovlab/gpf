import { Component, OnInit, Input, forwardRef, ViewChild,
         ChangeDetectorRef} from '@angular/core';
import { PhenoFilter } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider'
import { StateRestoreService } from '../store/state-restore.service'

@Component({
  selector: 'gpf-family-filters-block',
  templateUrl: './family-filters-block.component.html',
  styleUrls: ['./family-filters-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => FamilyFiltersBlockComponent) }]
})
export class FamilyFiltersBlockComponent extends QueryStateCollector implements OnInit {
  @Input() phenoFilters: Array<PhenoFilter>;
  @Input() datasetId: string;
  @ViewChild('tabset') ngbTabset;

  constructor(
    private stateRestoreService: StateRestoreService,
    private changeDetectorRef: ChangeDetectorRef
  ) {
    super();
  }

  ngOnInit() {
  }

  ngAfterViewInit() {
    this.stateRestoreService.state.subscribe(
      (state) => {
        console.log("families", state);
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

}
