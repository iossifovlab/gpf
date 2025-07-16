import { Component, OnInit, Input, Output, EventEmitter, Pipe, PipeTransform } from '@angular/core';

@Pipe({
    name: 'displayName',
    standalone: false
})
export class DisplayNamePipe implements PipeTransform {
  public transform(item: string, displayNames: Map<string, string>): string {
    return (displayNames[item] || item) as string;
  }
}

@Component({
    selector: 'gpf-checkbox-list',
    templateUrl: './checkbox-list.component.html',
    standalone: false
})
export class CheckboxListComponent implements OnInit {
  @Input() public title: string;
  @Input() public items: Set<string>;
  @Input() public selectedItems: Set<string>;
  @Input() public displayNames: Map<string, string> = new Map();
  @Output() public itemsUpdateEvent = new EventEmitter<Set<string>>();

  public ngOnInit(): void {
    if (!this.selectedItems) {
      this.selectAll();
    }
  }

  public emit(): void {
    this.itemsUpdateEvent.emit(this.selectedItems);
  }

  public selectNone(): void {
    this.selectedItems.clear();
    this.emit();
  }

  public selectAll(): void {
    this.selectedItems = new Set([...this.items]);
    this.emit();
  }

  public toggleItem(item: string): void {
    if (this.selectedItems.has(item)) {
      this.selectedItems.delete(item);
    } else {
      this.selectedItems.add(item);
    }
    this.emit();
  }
}
