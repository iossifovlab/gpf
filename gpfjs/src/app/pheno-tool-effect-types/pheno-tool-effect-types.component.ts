import { Component, Input, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import {
  PHENO_TOOL_ALL, PHENO_TOOL_OTHERS,
  PHENO_TOOL_CNV, PHENO_TOOL_LGDS,
  PHENO_TOOL_INITIAL_VALUES
} from './pheno-tool-effect-types';
import { take } from 'rxjs';
import {
  addEffectType,
  removeEffectType,
  selectEffectTypes,
  setEffectTypes
} from 'app/effect-types/effect-types.state';
import { resetErrors, setErrors } from 'app/common/errors.state';
import { cloneDeep } from 'lodash';

@Component({
    selector: 'gpf-pheno-tool-effect-types',
    templateUrl: './pheno-tool-effect-types.component.html',
    providers: [{ provide: Store, useClass: Store }],
    standalone: false
})
export class PhenoToolEffectTypesComponent implements OnInit {
  public phenoToolOthers: Set<string> = PHENO_TOOL_OTHERS;
  public phenoToolCNV: Set<string> = PHENO_TOOL_CNV;
  public phenoToolLGDs: Set<string> = PHENO_TOOL_LGDS;
  public initialEffectTypes: Set<string> = PHENO_TOOL_INITIAL_VALUES;

  public effectTypesButtons: Map<string, Set<string>>;
  public errors: string[] = [];
  public selectedEffectTypes: Set<string> = new Set();
  @Input() public variantTypes: Set<string> = new Set();

  public constructor(protected store: Store) {}

  public ngOnInit(): void {
    this.effectTypesButtons = new Map<string, Set<string>>();
    this.effectTypesButtons.set('ALL', new Set(PHENO_TOOL_ALL));
    this.effectTypesButtons.set('NONE', new Set());

    this.store.select(selectEffectTypes).pipe(take(1)).subscribe(effectTypesState => {
      if (effectTypesState.length) {
        this.selectedEffectTypes = new Set(effectTypesState);
      } else {
        this.selectedEffectTypes = this.initialEffectTypes;
      }
      this.setEffectTypes(this.selectedEffectTypes);
    });
  }

  public selectButtonGroup(groupId: string): void {
    const effectTypes: Set<string> = cloneDeep(this.effectTypesButtons.get(groupId));
    if (groupId === 'ALL' && !this.variantTypes.has('CNV')) {
      for (const effectType of PHENO_TOOL_CNV) {
        effectTypes.delete(effectType);
      }
    }
    this.setEffectTypes(effectTypes);
  }

  public setEffectTypes(effectTypes: Set<string>): void {
    this.selectedEffectTypes = new Set(effectTypes);
    this.validateState();
    this.store.dispatch(setEffectTypes({effectTypes: [...this.selectedEffectTypes]}));
  }

  public onEffectTypeChange(value: {checked: boolean; effectType: string}): void {
    if (value.checked && !this.selectedEffectTypes.has(value.effectType)) {
      this.selectedEffectTypes.add(value.effectType);
      this.validateState();
      this.store.dispatch(addEffectType({effectType: value.effectType}));
    } else if (!value.checked && this.selectedEffectTypes.has(value.effectType)) {
      this.selectedEffectTypes.delete(value.effectType);
      this.validateState();
      this.store.dispatch(removeEffectType({effectType: value.effectType}));
    }
  }

  private validateState(): void {
    this.errors = [];
    if (!this.selectedEffectTypes.size) {
      this.errors.push('Select at least one.');
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: 'effectTypes', errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: 'effectTypes'}));
    }
  }
}
