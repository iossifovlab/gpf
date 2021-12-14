import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { environment } from 'environments/environment';

@Component({
  selector: 'gpf-sorting-buttons',
  templateUrl: './sorting-buttons.component.html',
  styleUrls: ['./sorting-buttons.component.css']
})
export class SortingButtonsComponent implements OnInit {
  @Input() public id: string;
  @Output() public sortEvent = new EventEmitter<{id: string, order: string}>();

  public hideState = 0;
  public imgPathPrefix: string;

  public ngOnInit(): void {
    this.imgPathPrefix = environment.imgPathPrefix;
  }

  public emitSortEvent(order: string): void {
    this.sortEvent.emit({ id: this.id, order: order });
  }

  public resetHideState(): void {
    this.hideState = 0;
  }
}
