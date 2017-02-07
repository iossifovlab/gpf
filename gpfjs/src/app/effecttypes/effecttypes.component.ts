import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

import {
  CODING,
  NONCODING,
  CNV, ALL, LGDS, NONSYNONYMOUS, UTRS,
  EFFECT_TYPE_CHECK, EFFECT_TYPE_UNCHECK, EFFECT_TYPE_SET,
} from './effecttypes';
import { DatasetsState } from '../datasets/datasets';
import { GpfState } from '../store/gpf-store';


@Component({
  selector: 'gpf-effecttypes-column',
  template: `
    <div class="effectypes-col">
      <em>{{columnName}}</em>
      <div *ngFor="let effect of effectTypesLabels; let i=index" class="checkbox">
        <label>
          <input 
            #checkbox
            type="checkbox"
            [checked]="effectTypesValues[i]"
            (change)="checkEffectType(i, checkbox.checked); 
                      $event.stopPropagation()">
          {{effect}}
        </label>
      </div>
    </div>
  `
})
export class EffecttypesColumnComponent implements OnInit {
  @Input() effectTypes: Observable<string[]>;
  @Input() columnName: string;
  @Input() effectTypesLabels: string[];

  @Output('effectTypeEvent') effectTypeEvent = new EventEmitter<any>();

  effectTypesValues: boolean[];

  ngOnInit() {
    this.effectTypesValues = new Array<boolean>(this.effectTypesLabels.length);
    for (let i = 0; i < this.effectTypesValues.length; ++i) {
      this.effectTypesValues[i] = false;
    }

    this.effectTypes.subscribe(values => {
      for (let i = 0; i < this.effectTypesLabels.length; ++i) {
        if (values.indexOf(this.effectTypesLabels[i]) !== -1) {
          this.effectTypesValues[i] = true;
        } else {
          this.effectTypesValues[i] = false;
        }
      }

    });
  }

  checkEffectType(index: number, value: any) {
    if (index < 0 || index > this.effectTypesValues.length) {
      return;
    }

    this.effectTypeEvent.emit(
      {
        'effectType': this.effectTypesLabels[index],
        'checked': value
      });
  }
};

@Component({
  selector: 'gpf-effecttypes',
  templateUrl: './effecttypes.component.html',
  styleUrls: ['./effecttypes.component.css']
})
export class EffecttypesComponent implements OnInit {
  codingColumn: string[] = CODING;
  nonCodingColumn: string[] = NONCODING;
  cnvColumn: string[] = CNV;

  private effectTypesButtons: Map<string, string[]>;
  private selectedEffectTypes = new Map<string, boolean>();

  effectTypes: Observable<Array<string>>;
  datasetsState: Observable<DatasetsState>;
  hasCNV: Observable<boolean>;

  constructor(
    private store: Store<GpfState>
  ) {

    this.effectTypes = this.store.select('effectTypes');
    this.datasetsState = this.store.select('datasets');
    this.hasCNV = this.datasetsState.map(datasetsState => {
      if (!datasetsState || !datasetsState.selectedDataset) {
        return false;
      }
      return datasetsState.selectedDataset.genotypeBrowser.hasCNV;
    });
    this.initButtonGroups();
  }

  ngOnInit() {
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
    if (effectTypes) {
      this.store.dispatch({
        'type': EFFECT_TYPE_SET,
        'payload': effectTypes
      });
    }
  }

  onEffectTypeChange(value: any): void {
    if (value.checked) {
      this.store.dispatch({
        'type': EFFECT_TYPE_CHECK,
        'payload': value.effectType
      });
    } else {
      this.store.dispatch({
        'type': EFFECT_TYPE_UNCHECK,
        'payload': value.effectType
      });

    }
  }

}
