import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { EffectTypes } from './effecttypes';


@Component({
  selector: 'gpf-effecttypes-column',
  templateUrl: './effecttypes-column.component.html'
})
export class EffecttypesColumnComponent implements OnInit {
  @Input() effectTypes: EffectTypes;
  @Input() columnName: string;
  @Input() effectTypesLabels: Set<string>;

  @Output('effectTypeEvent') effectTypeEvent = new EventEmitter<any>();

  ngOnInit() {
  }

  checkEffectType(effectType: string, value: any) {
    if (!this.effectTypesLabels.has(effectType)) {
      return;
    }

    this.effectTypeEvent.emit({
      'effectType': effectType,
      'checked': value
    });
  }
}
