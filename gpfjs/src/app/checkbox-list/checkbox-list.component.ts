import { Component, OnInit, Input, Output, EventEmitter, Pipe, PipeTransform } from '@angular/core';

@Pipe({name: 'displayName'})
export class DisplayNamePipe implements PipeTransform {
  transform(item: string, displayNames: Map<string, string>, args?: any): string {
    return displayNames[item] || item;
  }
}

@Component({
  selector: 'gpf-checkbox-list',
  templateUrl: './checkbox-list.component.html',
  styleUrls: ['./checkbox-list.component.css']
})
export class CheckboxListComponent implements OnInit {

  @Input() title: string;
  @Input() items: Set<string>;
  @Input() selectedItems: Set<string>;
  @Input() displayNames: Map<string, string> = new Map();
  @Output() itemsUpdateEvent = new EventEmitter<Set<string>>();

  ngOnInit(): void {
    if (!this.selectedItems) {
      this.selectAll();
    }
  }

  emit(): void {
    this.itemsUpdateEvent.emit(this.selectedItems);
  }

  selectNone(): void {
    this.selectedItems.clear();
    this.emit();
  }

  selectAll(): void {
    this.selectedItems = new Set([...this.items]);
    this.emit();
  }

  toggleItem(item: string): void {
    this.selectedItems.has(item) ? this.selectedItems.delete(item) : this.selectedItems.add(item);
    this.emit();
  }
}
