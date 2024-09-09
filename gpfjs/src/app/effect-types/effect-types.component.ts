import { Component, OnInit, Input } from '@angular/core';
import { EffectTypes, CODING, NONCODING, CNV, ALL, LGDS, NONSYNONYMOUS, UTRS } from './effect-types';
import { ValidateNested } from 'class-validator';
import { PHENO_TOOL_CNV } from 'app/pheno-tool-effect-types/pheno-tool-effect-types';
import * as lodash from 'lodash';
import { addEffectType, removeEffectType, selectEffectTypes, setEffectTypes } from './effect-types.state';
import { take } from 'rxjs';
import { Store } from '@ngrx/store';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-effect-types',
  templateUrl: './effect-types.component.html'
})
export class EffectTypesComponent extends StatefulComponent implements OnInit {
  @Input() public variantTypes: Set<string> = new Set();

  public codingColumn: Set<string> = CODING;
  public nonCodingColumn: Set<string> = NONCODING;
  public cnvColumn: Set<string> = CNV;

  @ValidateNested()
  public effectTypes = new EffectTypes();
  public effectTypesButtons: Map<string, Set<string>>;

  public constructor(protected store: Store) {
    super(store, 'effectTypes', selectEffectTypes);
    this.initButtonGroups();
  }

  public ngOnInit(): void {
    this.store.select(selectEffectTypes).pipe(take(1)).subscribe(effectTypesState => {
      this.effectTypes = new EffectTypes();
      this.effectTypes.selected = new Set(effectTypesState);
      super.ngOnInit();
    });
  }

  public selectInitialValues(): void {
    this.selectButtonGroup('LGDS');
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
    if (groupId === 'PHENO_TOOL_ALL' && !this.variantTypes.has('CNV')) {
      for (const effectType of PHENO_TOOL_CNV) {
        effectTypes.delete(effectType);
      }
    }
    this.setEffectTypes(effectTypes);
  }

  public setEffectTypes(effectTypes: Set<string>): void {
    this.effectTypes.selected = new Set(effectTypes);
    this.store.dispatch(setEffectTypes({effectTypes: [...this.effectTypes.selected]}));
  }

  public onEffectTypeChange(value: {checked: boolean; effectType: string}): void {
    if (value.checked && !this.effectTypes.selected.has(value.effectType)) {
      this.effectTypes.selected.add(value.effectType);
      this.store.dispatch(addEffectType({effectType: value.effectType}));
    } else if (!value.checked && this.effectTypes.selected.has(value.effectType)) {
      this.effectTypes.selected.delete(value.effectType);
      this.store.dispatch(removeEffectType({effectType: value.effectType}));
    }
  }
}
