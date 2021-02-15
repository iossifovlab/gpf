import { Component, OnInit, forwardRef } from '@angular/core';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';
import { FamilyTypes } from './family-type';

@Component({
  selector: 'gpf-family-type-filter',
  templateUrl: './family-type-filter.component.html',
  styleUrls: ['./family-type-filter.component.css'],
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => FamilyTypeFilterComponent)
  }]
})
export class FamilyTypeFilterComponent extends QueryStateWithErrorsProvider implements OnInit {

  familyTypes = new FamilyTypes();
  allFamilyTypes = ['trio', 'quad', 'multigenerational', 'simplex', 'multiplex'];

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit(): void {
    this.stateRestoreService.getState(this.constructor.name).take(1).subscribe((state) => {
        if (state['familyTypes']) {
          this.familyTypes.familyTypes = state['familyTypes'];
        }
      }
    );
  }

  getState() {
    return this.validateAndGetState(this.familyTypes).map(familyTypes => {
      return { familyTypes: familyTypes.familyTypes };
    });
  }

  checkFamilyType(familyType: string, value: boolean): void {
    console.log(familyType, value);
    if (this.allFamilyTypes.indexOf(familyType) !== -1) {
      if (!value) {
        this.familyTypes.familyTypes.push(familyType);
      } else {
        this.familyTypes.familyTypes.splice(this.familyTypes.familyTypes.indexOf(familyType), 1);
      }
    }
    console.log(this.familyTypes.familyTypes);
  }
}
