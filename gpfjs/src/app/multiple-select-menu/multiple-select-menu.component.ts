import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { Component, ElementRef, EventEmitter, Input, OnChanges, Output, ViewChild } from '@angular/core';
import { AgpColumn } from 'app/autism-gene-profiles-table/autism-gene-profiles-table';
import { environment } from 'environments/environment';

@Component({
  selector: 'gpf-multiple-select-menu',
  templateUrl: './multiple-select-menu.component.html',
  styleUrls: ['./multiple-select-menu.component.css']
})
export class MultipleSelectMenuComponent implements OnChanges {
  @Input() public columns: AgpColumn[];
  @Output() public applyEvent = new EventEmitter<void>();
  @Output() public reorderEvent = new EventEmitter<string[]>();
  @ViewChild('searchInput') public searchInput: ElementRef;

  public buttonLabel = 'Uncheck all';
  public searchText: string;
  public filteredColumns: AgpColumn[];
  public searchPlaceholder: string;

  public imgPathPrefix = environment.imgPathPrefix;

  public ngOnChanges(): void {
    this.refresh();
  }

  public refresh(): void {
    this.searchText = '';
    this.updateButtonLabel();
    this.filteredColumns = this.columns;

    // focus search input field
    this.waitForSearchInputToLoad().then(() => {
      this.searchInput.nativeElement.focus();
    });
  }

  public toggleCheckingAll(): void {
    if (this.buttonLabel === 'Uncheck all') {
      this.buttonLabel = 'Check all';
      this.columns.map(col => {
        col.visibility = false;
      });
    } else if (this.buttonLabel === 'Check all') {
      this.buttonLabel = 'Uncheck all';
      this.columns.map(col => {
        col.visibility = true;
      });
    }
    this.apply();
  }

  public toggleItem(column: AgpColumn, $event: Event): void {
    if (!($event.target instanceof HTMLInputElement)) {
      return;
    }
    column.visibility = $event.target.checked;
    this.updateButtonLabel();
    this.apply();
  }

  public apply(): void {
    this.applyEvent.emit();
  }

  private updateButtonLabel(): void {
    this.buttonLabel = this.columns.filter(col => col.visibility).length > 0 ? 'Uncheck all' : 'Check all';
  }

  public drop(event: CdkDragDrop<string[]>): void {
    moveItemInArray(this.columns, event.previousIndex, event.currentIndex);
    this.apply();
    this.reorderEvent.emit(this.filteredColumns.map(col => col.id));
  }

  public filterItems(substring: string): void {
    this.filteredColumns = this.columns.filter(col => col.displayName.toLowerCase().includes(substring.toLowerCase()));
  }

  private async waitForSearchInputToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.searchInput !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 50);
    });
  }
}
