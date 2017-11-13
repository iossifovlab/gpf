import { Component, OnInit, Input, Output, EventEmitter, OnChanges } from '@angular/core';
import { EffectTypes } from './effecttypes';


@Component({
  selector: 'gpf-effecttypes-column',
  templateUrl: './effecttypes-column.component.html'
})
export class EffecttypesColumnComponent implements OnInit, OnChanges {
  @Input() effectTypes: EffectTypes;
  @Input() columnName: string;
  @Input() effectTypesLabels: string[];

  @Output('effectTypeEvent') effectTypeEvent = new EventEmitter<any>();

  effectTypesValues: boolean[];

  ngOnChanges() {
    this.effectTypesValues = new Array<boolean>(this.effectTypesLabels.length);
    for (let i = 0; i < this.effectTypesValues.length; ++i) {
      this.effectTypesValues[i] = false;
    }

    for (let value of this.effectTypes.selected) {
      for (let i = 0; i < this.effectTypesLabels.length; ++i) {
        if (value.indexOf(this.effectTypesLabels[i]) !== -1) {
          this.effectTypesValues[i] = true;
        } else {
          this.effectTypesValues[i] = false;
        }
      }
    }
  }

  ngOnInit() {
  }

  checkEffectType(index: number, value: any) {
    if (index < 0 || index > this.effectTypesValues.length) {
      return;
    }

    this.effectTypesValues[index] = value;
    this.effectTypeEvent.emit({
      'effectType': this.effectTypesLabels[index],
      'checked': value
    });
  }
};
