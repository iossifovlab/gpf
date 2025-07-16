import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
    selector: 'gpf-sorting-buttons',
    templateUrl: './sorting-buttons.component.html',
    styleUrls: ['./sorting-buttons.component.css'],
    standalone: false
})
export class SortingButtonsComponent {
  @Input() public id: string;
  @Input() public sortState = 0;
  @Output() public sortEvent = new EventEmitter<{id: string; order: string}>();
  private order = 'desc';

  public emitSort(): void {
    this.sortState = this.sortState === 1 ? -1 : 1;
    this.sortEvent.emit({id: this.id, order: this.order});
    this.order = this.order === 'desc' ? 'asc' : 'desc';
  }

  public resetSortState(): void {
    this.sortState = 0;
  }
}
