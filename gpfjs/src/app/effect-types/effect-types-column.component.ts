import { Component, Input, Output, EventEmitter } from '@angular/core';
import { EffectTypes } from './effect-types';

@Component({
  selector: 'gpf-effect-types-column',
  templateUrl: './effect-types-column.component.html'
})
export class EffecttypesColumnComponent {
  @Input() effectTypes: EffectTypes;
  @Input() columnName: string;
  @Input() effectTypesLabels: Set<string>;
  @Output('effectTypeEvent') effectTypeEvent = new EventEmitter<any>();

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
