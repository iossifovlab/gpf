import { Component, OnInit, Input, Output, EventEmitter, forwardRef } from '@angular/core';

import { Observable } from 'rxjs';

import { EffectTypes, CODING, NONCODING, CNV, ALL, LGDS, NONSYNONYMOUS, UTRS } from './effecttypes';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { StateRestoreService } from '../store/state-restore.service';


@Component({
  selector: 'gpf-effecttypes',
  templateUrl: './effecttypes.component.html',
  styleUrls: ['./effecttypes.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => EffecttypesComponent) }]
})
export class EffecttypesComponent extends QueryStateWithErrorsProvider implements OnInit {
  @Input()
  hasCNV = false;

  codingColumn: string[] = CODING;
  nonCodingColumn: string[] = NONCODING;
  cnvColumn: string[] = CNV;

  effectTypesButtons: Map<string, string[]>;
  private selectedEffectTypes = new Map<string, boolean>();

  effectTypes = new EffectTypes();

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
    this.initButtonGroups();
  }

  ngOnInit() {
    this.selectInitialValues();

    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['effectTypes']) {
          this.selectEffectTypesSet(state['effectTypes']);
        }
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
    this.effectTypesButtons.set('NONSYNONYMOUS', NONSYNONYMOUS);
    this.effectTypesButtons.set('UTRS', UTRS);
  }

  selectButtonGroup(groupId: string): void {
    let effectTypes: string[] = this.effectTypesButtons.get(groupId);
    this.selectEffectTypesSet(effectTypes);
  }

  selectEffectTypesSet(effectTypes): void {
    if (effectTypes) {
      this.effectTypes.selected = effectTypes.slice();
    }
  }

  onEffectTypeChange(value: any): void {
    if (value.checked && this.effectTypes.selected.indexOf(value.effectType) === -1) {
      this.effectTypes.selected.push(value.effectType);
    } else if (!value.checked && this.effectTypes.selected.indexOf(value.effectType) !== -1) {
      this.effectTypes.selected = this.effectTypes.selected.filter(v => v !== value.effectType);
    }
  }

  getState() {
    return this.validateAndGetState(this.effectTypes)
      .map(effectTypes => ({
        effectTypes: effectTypes.selected
      }));
  }

}
