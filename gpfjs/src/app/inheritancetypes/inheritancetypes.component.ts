import { Component, Input, OnInit, OnChanges, forwardRef } from '@angular/core';
import { InheritanceTypes, inheritanceTypeDisplayNames  } from './inheritancetypes';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-inheritancetypes',
  templateUrl: './inheritancetypes.component.html',
  styleUrls: ['./inheritancetypes.component.css'],
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => InheritancetypesComponent )
  }]
})
export class InheritancetypesComponent extends QueryStateWithErrorsProvider
    implements OnInit, OnChanges {

  @Input()
  availableInheritanceTypes: Array<string>;

  @Input()
  selectedInheritanceTypes: Array<string>;

  inheritanceTypes: InheritanceTypes;

  constructor(
    private stateRestoreService: StateRestoreService
  ) { 
    super();
  }

  ngOnInit() { 
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['inheritanceTypes']) {
          this.inheritanceTypes.selected = state['inheritanceTypes'];
        }
      });
  }

  ngOnChanges() {
    this.inheritanceTypes = new InheritanceTypes(
      this.availableInheritanceTypes, this.selectedInheritanceTypes
    );
  }

  getState() {
    return this.validateAndGetState(this.inheritanceTypes)
      .map(inheritanceTypes => ({
        inheritanceTypes: Array.from(inheritanceTypes.selected)
      }));
  }

  checkInheritanceType(inheritanceType: string) {
    if (this.inheritanceTypes.selected.has(inheritanceType)){
      this.inheritanceTypes.selected.delete(inheritanceType);
    }
    else {
      this.inheritanceTypes.selected.add(inheritanceType);
    }
  }

  getDisplayName(inheritanceType: string) {
    return inheritanceTypeDisplayNames[inheritanceType] || inheritanceType;
  }

  selectAll() {
    this.inheritanceTypes.selected = new Set(this.inheritanceTypes.available);
  }

  selectNone() {
    this.inheritanceTypes.selected = new Set();
  }

}
