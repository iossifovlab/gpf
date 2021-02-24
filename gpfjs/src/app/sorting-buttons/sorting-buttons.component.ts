import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { environment } from 'environments/environment';

@Component({
  selector: 'gpf-sorting-buttons',
  templateUrl: './sorting-buttons.component.html',
  styleUrls: ['./sorting-buttons.component.css']
})
export class SortingButtonsComponent implements OnInit {
  @Input() id: string;
  @Output() sortEvent = new EventEmitter<{id: string, order: string}>();
  private hideState = 0;

  constructor() { }

  ngOnInit(): void { }

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
