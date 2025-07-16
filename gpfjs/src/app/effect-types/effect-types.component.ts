import { Component, OnInit, Input } from '@angular/core';
import {
  CODING, NONCODING, CNV, ALL, LGDS,
  NONSYNONYMOUS, UTRS
} from './effect-types';
import * as lodash from 'lodash';
import { addEffectType, removeEffectType, selectEffectTypes, setEffectTypes } from './effect-types.state';
import { take } from 'rxjs';
import { Store } from '@ngrx/store';
import { setErrors, resetErrors } from 'app/common/errors.state';

@Component({
  selector: 'gpf-effect-types',
  templateUrl: './effect-types.component.html',
  styleUrls: ['./effect-types.css'],
  standalone: false
})
export class EffectTypesComponent implements OnInit {
  @Input() public variantTypes: Set<string> = new Set();

  public codingColumn: Set<string> = CODING;
  public nonCodingColumn: Set<string> = NONCODING;
  public cnvColumn: Set<string> = CNV;

  public selectedEffectTypes: Set<string> = new Set();

  public effectTypesButtons: Map<string, Set<string>>;
  public errors: string[] = [];

  public constructor(protected store: Store) {
    this.initButtonGroups();
  }

  public ngOnInit(): void {
    this.store.select(selectEffectTypes).pipe(take(1)).subscribe(effectTypesState => {
      this.selectedEffectTypes = new Set(effectTypesState);
      this.validateState();
    });
  }

  private initButtonGroups(): void {
    this.effectTypesButtons = new Map<string, Set<string>>();
    this.effectTypesButtons.set('ALL', new Set(ALL));
    this.effectTypesButtons.set('NONE', new Set());
    this.effectTypesButtons.set('LGDS', new Set(LGDS));
    this.effectTypesButtons.set('CODING', new Set(CODING));
    this.effectTypesButtons.set('NONSYNONYMOUS', new Set(NONSYNONYMOUS));
    this.effectTypesButtons.set('UTRS', new Set(UTRS));
  }

  public selectButtonGroup(groupId: string): void {
    const effectTypes: Set<string> = lodash.cloneDeep(this.effectTypesButtons.get(groupId));
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
          componentId: 'effectTypes', errors: lodash.cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: 'effectTypes'}));
    }
  }
}
