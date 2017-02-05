import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { DatasetService } from '../dataset/dataset.service';
import { IdName } from '../common/idname';

import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

import {
  CODING,
  NONCODING,
  CNV, ALL, LGDS, NONSYNONYMOUS, UTRS,
  EFFECT_TYPE_CHECK, EFFECT_TYPE_UNCHECK, EFFECT_TYPE_SET,
} from './effecttypes';


@Component({
  selector: 'gpf-effecttypes-column',
  template: `
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
      console.log('effectTypes changed...', values);
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

    console.log('checking ', this.effectTypesLabels[index], value);
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

  buttonGroups: IdName[];
  columnGroups: IdName[];

  effectTypesColumns: Map<string, string[]>;

  private effectTypesButtons: Map<string, string[]>;
  private selectedEffectTypes = new Map<string, boolean>();

  effectTypes: Observable<Array<string>>;

  constructor(
    private datasetService: DatasetService,
    private store: Store<any>
  ) {

    this.effectTypes = this.store.select('effectTypes');
    console.log(this.effectTypes);

    this.initButtonGroups();
    this.initColumnGroups();
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

    this.buttonGroups = [
      { id: 'ALL', name: 'All' },
      { id: 'NONE', name: 'None' },
      { id: 'LGDS', name: 'LGDs' },
      { id: 'NONSYNONYMOUS', name: 'Nonsynonymous' },
      { id: 'UTRS', name: 'UTRs' },
    ];
  }

  private initColumnGroups(): void {
    this.effectTypesColumns = new Map<string, string[]>();

    this.effectTypesColumns.set('CODING', CODING);
    this.effectTypesColumns.set('NONCODING', NONCODING);
    this.effectTypesColumns.set('CNV', CNV);

    this.columnGroups = [
      { id: 'CODING', name: 'Coding' },
      { id: 'NONCODING', name: 'Noncoding' },
      { id: 'CNV', name: 'CNV' },
    ];

  }

  selectButtonGroup(groupId: string): void {
    let effectTypes: string[] = this.effectTypesButtons.get(groupId);
    if (effectTypes) {
      console.log('set effect types event: ', effectTypes);
      this.store.dispatch({
        'type': EFFECT_TYPE_SET,
        'payload': effectTypes
      });
    }
  }

  onEffectTypeChange(value: any): void {
    console.log('onEffectTypeChange: ', value);
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
