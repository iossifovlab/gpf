import {
  Input, Component, OnInit, OnChanges, SimpleChanges, forwardRef
} from '@angular/core';

import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';
import { DatasetsService } from '../datasets/datasets.service';

import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';

@Component({
  selector: 'gpf-varianttypes',
  templateUrl: './varianttypes.component.html',
  styleUrls: ['./varianttypes.component.css'],
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => VarianttypesComponent)
  }]
})
export class VarianttypesComponent extends QueryStateWithErrorsProvider
    implements OnInit, OnChanges {

  @Input()
  variantTypes: Set<string> = new Set([]);

  @Input()
  @Validate(SetNotEmpty, {message: 'select at least one'})
  selectedVariantTypes: Set<string> = new Set([]);

  constructor(
    private stateRestoreService: StateRestoreService,
    private datasetsService: DatasetsService
  ) {
    super();
  }

  ngOnInit() {
    this.selectedVariantTypes = new Set();
  }

  ngOnChanges(changes: SimpleChanges) {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['variantTypes']) {
          this.selectedVariantTypes = new Set(state['variantTypes'] as string[]);
        }
      });
  }

  selectAll(): void {
    this.selectedVariantTypes = new Set(this.variantTypes);
  }

  selectNone(): void {
    this.selectedVariantTypes = new Set();
  }

  variantTypesCheckValue(variantType: string, value: boolean): void {
    if (variantType === 'sub' || variantType === 'ins' || variantType === 'del' ||
        variantType === 'CNV' || variantType === 'complex' || variantType === 'TR') {
      if (!value) {
        this.selectedVariantTypes.add(variantType);
      } else {
        this.selectedVariantTypes.delete(variantType);
      }
    }
  }

  getState() {
    return this.validateAndGetState(this)
      .map(_ => ({ 'variantTypes': Array.from(this.selectedVariantTypes) }));
  }
}
