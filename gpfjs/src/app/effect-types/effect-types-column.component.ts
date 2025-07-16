import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
    selector: 'gpf-effect-types-column',
    templateUrl: './effect-types-column.component.html',
    standalone: false
})
export class EffecttypesColumnComponent {
  @Input() public effectTypes: Set<string>;
  @Input() public columnName: string;
  @Input() public effectTypesLabels: Set<string>;
  @Output() public effectTypeEvent = new EventEmitter<{effectType: string; checked: boolean}>();

  public checkEffectType(effectType: string, value: boolean): void {
    if (!this.effectTypesLabels.has(effectType)) {
      return;
    }

    this.effectTypeEvent.emit({
      effectType: effectType,
      checked: value
    });
  }
}
