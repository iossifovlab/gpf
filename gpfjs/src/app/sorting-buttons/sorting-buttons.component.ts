import { Component, EventEmitter, Input, Output } from '@angular/core';
import { environment } from 'environments/environment';

@Component({
  selector: 'gpf-sorting-buttons',
  templateUrl: './sorting-buttons.component.html',
  styleUrls: ['./sorting-buttons.component.css']
})
export class SortingButtonsComponent {
  @Input() id: string;
  @Output() sortEvent = new EventEmitter<{id: string, order: string}>();
  hideState = 0;

  get imgPathPrefix(): string {
    return environment.imgPathPrefix;
  }

  emitSortEvent(order: string): void {
    this.sortEvent.emit({id: this.id, order: order});
  }

  resetHideState(): void {
    this.hideState = 0;
  }
}
