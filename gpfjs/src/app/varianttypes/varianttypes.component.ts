import {
  Input, Component, OnInit, OnChanges, SimpleChanges, forwardRef
} from '@angular/core';

import { Observable } from 'rxjs';

import { VariantTypes } from './varianttypes';
import { QueryStateProvider } from '../query/query-state-provider';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { StateRestoreService } from '../store/state-restore.service';
import { DatasetsService } from '../datasets/datasets.service';

@Component({
  selector: 'gpf-varianttypes',
  templateUrl: './varianttypes.component.html',
  styleUrls: ['./varianttypes.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => VarianttypesComponent) }]
})
export class VarianttypesComponent extends QueryStateProvider
    implements OnInit, OnChanges {

  variantTypes = new VariantTypes();
  @Input()
  hasCNV = false;

  errors: string[];
  flashingAlert = false;

  constructor(
    private stateRestoreService: StateRestoreService,
    private datasetsService: DatasetsService
  ) {
    super();
  }

  ngOnInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .subscribe(state => {
        if (state['variantTypes']) {
          this.variantTypes.selected = new Set(state['variantTypes'] as string[]);
        }
      });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['hasCNV']) {
      this.selectAll();
    }
  }

  selectAll(): void {
    let selected = new Set(['sub', 'ins', 'del']);
    if (this.hasCNV) {
      selected.add('CNV');
    }
    this.variantTypes.selected = selected;
  }

  selectNone(): void {
    this.variantTypes.selected = new Set();
  }

  variantTypesCheckValue(variantType: string, value: boolean): void {
    if (variantType === 'sub' || variantType === 'ins' || variantType === 'del' || variantType === 'CNV') {
      if (value) {
        this.variantTypes.selected.add(variantType);
      } else {
        this.variantTypes.selected.delete(variantType);
      }
    }
  }

  getState() {
    console.log("getstate called...");
    return toValidationObservable(this.variantTypes)
      .map(variantTypes => ({
        variantTypes: Array.from(variantTypes.selected)
      }))
      .catch(errors => {
        this.errors = validationErrorsToStringArray(errors);
        this.flashingAlert = true;
        setTimeout(() => { this.flashingAlert = false; }, 1000);

        return Observable.throw(`${this.constructor.name}: invalid state`);
      });
  }
}
