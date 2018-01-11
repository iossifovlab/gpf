import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { EffectTypes } from './effecttypes';


@Component({
  selector: 'gpf-effecttypes-column',
  templateUrl: './effecttypes-column.component.html'
})
export class EffecttypesColumnComponent implements OnInit {
  @Input() effectTypes: EffectTypes;
  @Input() columnName: string;
  @Input() effectTypesLabels: string[];

  @Output('effectTypeEvent') effectTypeEvent = new EventEmitter<any>();

  ngOnInit() {
  }

  checkEffectType(index: number, value: any) {
    if (index < 0 || index > this.effectTypesLabels.length) {
      return;
    }

    this.effectTypeEvent.emit({
      'effectType': this.effectTypesLabels[index],
      'checked': value
    });
  }
};
