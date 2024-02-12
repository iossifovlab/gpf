import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import _ from 'lodash';

@Component({
  selector: 'gpf-family-tags',
  templateUrl: './family-tags.component.html',
  styleUrls: ['./family-tags.component.css']
})
export class FamilyTagsComponent implements OnInit {
  @Input() public numOfRows: number | string;
  @Input() public numOfCols: number;
  @Input() public tags = [];
  @Output() public chooseMode = new EventEmitter<boolean>();
  @Output() public updateTagsLists = new EventEmitter();

  public selectedTags: string[] = [];
  public deselectedTags: string[] = [];
  public filtersButtonsState: Record<string, number> = {};
  public tagIntersection = true; // mode "And"

  public onChooseMode(intersected: boolean = true): void {
    this.tagIntersection = intersected;
    this.chooseMode.emit(intersected);
  }

  public onUpdateTags(): void {
    this.updateTagsLists.next({selected: this.selectedTags, deselected: this.deselectedTags});
  }

  public ngOnInit(): void {
    this.tags.forEach((tag: string) => {
      this.filtersButtonsState[tag] = 0;
    });
  }

  public selectFilter(tag: string): void {
    if (this.filtersButtonsState[tag] === 1) {
      this.filtersButtonsState[tag] = 0;
    } else {
      this.filtersButtonsState[tag] = 1;
    }
    this.updateSelectedTagsList(tag);
  }

  public deselectFilter(tag: string): void {
    if (this.filtersButtonsState[tag] === -1) {
      this.filtersButtonsState[tag] = 0;
    } else {
      this.filtersButtonsState[tag] = -1;
    }
    this.updateDeselectedTagsList(tag);
  }

  public clearFilters(): void {
    this.selectedTags = [];
    this.deselectedTags = [];
    this.filtersButtonsState = _.mapValues(this.filtersButtonsState, () => 0);

    this.onUpdateTags();
  }

  public updateSelectedTagsList(tag: string): void {
    if (!this.selectedTags.includes(tag)) {
      this.selectedTags.push(tag);
    } else {
      const index = this.selectedTags.indexOf(tag);
      this.selectedTags.splice(index, 1);
    }
    if (this.deselectedTags.includes(tag)) {
      const index = this.deselectedTags.indexOf(tag);
      this.deselectedTags.splice(index, 1);
    }
    this.onUpdateTags();
  }

  public updateDeselectedTagsList(tag: string): void {
    if (!this.deselectedTags.includes(tag)) {
      this.deselectedTags.push(tag);
    } else {
      const index = this.deselectedTags.indexOf(tag);
      this.deselectedTags.splice(index, 1);
    }
    if (this.selectedTags.includes(tag)) {
      const index = this.selectedTags.indexOf(tag);
      this.selectedTags.splice(index, 1);
    }
    this.onUpdateTags();
  }
}
