import { Component, OnInit, Input } from '@angular/core';
import { EffectTypes, CODING, NONCODING, CNV, ALL, LGDS, NONSYNONYMOUS, UTRS } from './effecttypes';
import { Observable } from 'rxjs';
import { validate } from 'class-validator';
import { Select, Store } from '@ngxs/store';
import { EffecttypesState, EffectTypeModel, AddEffectType, RemoveEffectType } from './effecttypes.state';

@Component({
  selector: 'gpf-effecttypes',
  templateUrl: './effecttypes.component.html',
  styleUrls: ['./effecttypes.component.css'],
})
export class EffecttypesComponent implements OnInit {

  @Input() variantTypes: Set<string> = new Set([]);

  codingColumn: string[] = CODING;
  nonCodingColumn: string[] = NONCODING;
  cnvColumn: string[] = CNV;

  effectTypesButtons: Map<string, string[]>;
  errors: string[] = [];
  effectTypes = new EffectTypes();
  @Select(EffecttypesState) state$: Observable<EffectTypeModel>;

  constructor(private store: Store) {
    this.initButtonGroups();
  }

  ngOnInit() {
    this.selectInitialValues();

    this.store.selectOnce(state => state.effecttypesState).subscribe(state => {
      for (const effectType of state.effectTypes) {
        this.onEffectTypeChange({checked: true, effectType: effectType});
      }
    });

    this.state$.subscribe(() => {
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  selectInitialValues() {
    this.selectButtonGroup('LGDS');
  }

  private initButtonGroups(): void {
    this.effectTypesButtons = new Map<string, string[]>();

    this.effectTypesButtons.set('ALL', ALL);
    this.effectTypesButtons.set('NONE', []);
    this.effectTypesButtons.set('LGDS', LGDS);
    this.effectTypesButtons.set('CODING', CODING);
    this.effectTypesButtons.set('NONSYNONYMOUS', NONSYNONYMOUS);
    this.effectTypesButtons.set('UTRS', UTRS);
  }

  selectButtonGroup(groupId: string): void {
    const effectTypes: string[] = this.effectTypesButtons.get(groupId);
    this.selectEffectTypesSet(effectTypes);
  }

  selectEffectTypesSet(effectTypes: string[]): void {
    if (!effectTypes) {
      return;
    }

    for (const effectType of this.effectTypes.selected) {
      this.store.dispatch(new RemoveEffectType(effectType));
    }

    this.effectTypes.selected = effectTypes.slice();

    for (const effectType of effectTypes) {
      this.store.dispatch(new AddEffectType(effectType));
    }
  }

  onEffectTypeChange(value: any): void {
    if (value.checked && this.effectTypes.selected.indexOf(value.effectType) === -1) {
      this.effectTypes.selected.push(value.effectType);
      this.store.dispatch(new AddEffectType(value.effectType));
    } else if (!value.checked && this.effectTypes.selected.indexOf(value.effectType) !== -1) {
      this.effectTypes.selected = this.effectTypes.selected.filter(v => v !== value.effectType);
      this.store.dispatch(new RemoveEffectType(value.effectType));
    }
  }
}
