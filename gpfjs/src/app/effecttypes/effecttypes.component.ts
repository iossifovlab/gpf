import { Component, OnInit, Input } from '@angular/core';
import { EffectTypes, CODING, NONCODING, CNV, ALL, LGDS, NONSYNONYMOUS, UTRS } from './effecttypes';
import { ValidateNested } from 'class-validator';
import { Store } from '@ngxs/store';
import { EffecttypesState, AddEffectType, RemoveEffectType, SetEffectTypes } from './effecttypes.state';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-effecttypes',
  templateUrl: './effecttypes.component.html',
  styleUrls: ['./effecttypes.component.css'],
})
export class EffecttypesComponent extends StatefulComponent implements OnInit {

  @Input() variantTypes: Set<string> = new Set([]);

  codingColumn: Set<string> = CODING;
  nonCodingColumn: Set<string> = NONCODING;
  cnvColumn: Set<string> = CNV;

  @ValidateNested()
  effectTypes = new EffectTypes();
  effectTypesButtons: Map<string, Set<string>>;

  constructor(protected store: Store) {
    super(store, EffecttypesState, 'effectTypes');
    this.initButtonGroups();
  }

  ngOnInit() {
    super.ngOnInit();
    this.store.selectOnce(state => state.effecttypesState).subscribe(state => {
      if (state.effectTypes.length) {
        for (const effectType of state.effectTypes) {
          this.onEffectTypeChange({checked: true, effectType: effectType});
        }
      } else {
        this.selectInitialValues();
      }
    });
  }

  selectInitialValues() {
    this.selectButtonGroup('LGDS');
  }

  private initButtonGroups(): void {
    this.effectTypesButtons = new Map<string, Set<string>>();
    this.effectTypesButtons.set('ALL', ALL);
    this.effectTypesButtons.set('NONE', new Set());
    this.effectTypesButtons.set('LGDS', LGDS);
    this.effectTypesButtons.set('CODING', CODING);
    this.effectTypesButtons.set('NONSYNONYMOUS', NONSYNONYMOUS);
    this.effectTypesButtons.set('UTRS', UTRS);
  }

  selectButtonGroup(groupId: string): void {
    const effectTypes: Set<string> = this.effectTypesButtons.get(groupId);
    this.setEffectTypes(effectTypes);
  }

  setEffectTypes(effectTypes: Set<string>) {
    this.effectTypes.selected = effectTypes;
    this.store.dispatch(new SetEffectTypes(effectTypes));
  }

  onEffectTypeChange(value: any): void {
    if (value.checked && !this.effectTypes.selected.has(value.effectType)) {
      this.effectTypes.selected.add(value.effectType);
      this.store.dispatch(new AddEffectType(value.effectType));
    } else if (!value.checked && this.effectTypes.selected.has(value.effectType)) {
      this.effectTypes.selected.delete(value.effectType);
      this.store.dispatch(new RemoveEffectType(value.effectType));
    }
  }
}
