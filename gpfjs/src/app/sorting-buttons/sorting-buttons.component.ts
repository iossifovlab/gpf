import { Component, EventEmitter, Input, Output } from '@angular/core';
import { environment } from 'environments/environment';

@Component({
  selector: 'gpf-sorting-buttons',
  templateUrl: './sorting-buttons.component.html',
  styleUrls: ['./sorting-buttons.component.css']
})
export class SortingButtonsComponent {
  @Input() public id: string;
  @Input() public hideState = 0;
  @Output() public sortEvent = new EventEmitter<{id: string, order: string}>();
  private order = 'desc';
  public imgPathPrefix = environment.imgPathPrefix;

  public emitSortEvent(order: string): void {
    this.sortEvent.emit({ id: this.id, order: order });
  }

  public emitSort() {
    this.hideState = (this.hideState === 1 ? -1 : 1);
    this.sortEvent.emit({id: this.id, order: this.order});
    this.order = (this.order === 'desc' ? 'asc' : 'desc');
  }

  public resetHideState(): void {
    this.hideState = 0;
  }
}
