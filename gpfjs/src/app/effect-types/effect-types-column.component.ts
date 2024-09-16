import { Component, Input, Output, EventEmitter } from '@angular/core';
import { EffectTypes } from './effect-types';

@Component({
  selector: 'gpf-effect-types-column',
  templateUrl: './effect-types-column.component.html'
})
export class EffecttypesColumnComponent {
  @Input() public effectTypes: EffectTypes;
  @Input() public columnName: string;
  @Input() public effectTypesLabels: Set<string>;
  @Output() public effectTypeEvent = new EventEmitter<{effectType: string; checked: boolean}>();

  public checkEffectType(effectType: string, value: boolean): void {
    console.log(this.effectTypesLabels)
    if (!this.effectTypesLabels.has(effectType)) {
      return;
    }

    this.effectTypeEvent.emit({
      effectType: effectType,
      checked: value
    });
  }
}
