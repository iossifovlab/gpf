import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { initialState, selectFamilyTags, setFamilyTags } from './family-tags.state';
import { Store } from '@ngrx/store';
import { take } from 'rxjs';
import { cloneDeep } from 'lodash';
import { FamilyTags } from './family-tags';

@Component({
  selector: 'gpf-family-tags',
  templateUrl: './family-tags.component.html',
  styleUrls: ['./family-tags.component.css']
})
export class FamilyTagsComponent implements OnInit {
  @Input() public numOfCols: number;
  @Input() public tags = [];
  @Output() public chooseMode = new EventEmitter<boolean>();
  @Output() public updateTagsLists = new EventEmitter();

  public selectedTags: string[] = [];
  public deselectedTags: string[] = [];
  public filtersButtonsState: Record<string, number> = {};
  public tagIntersection = true; // mode "And"
  public familyTags: FamilyTags = cloneDeep(initialState);

  public constructor(protected store: Store) { }

  public ngOnInit(): void {
    this.tags.forEach((tag: string) => {
      this.filtersButtonsState[tag] = 0;
    });

    this.store
      .select(selectFamilyTags)
      .pipe(take(1))
      .subscribe((familyTags: FamilyTags) => {
        const familyTagsClone = cloneDeep(familyTags);
        this.restoreFamilyTags(
          familyTagsClone.selectedFamilyTags,
          familyTagsClone.deselectedFamilyTags,
          familyTagsClone.tagIntersection
        );
      });
  }

  public restoreFamilyTags(selectedTags: string[], deselectedTags: string[], intersection: boolean): void {
    this.selectedTags = selectedTags;
    this.selectedTags.forEach(tag => {
      this.filtersButtonsState[tag] = 1;
    });

    this.deselectedTags = deselectedTags;
    this.deselectedTags.forEach(tag => {
      this.filtersButtonsState[tag] = -1;
    });

    this.tagIntersection = intersection;

    this.familyTags.deselectedFamilyTags = deselectedTags;
    this.familyTags.selectedFamilyTags = selectedTags;
    this.familyTags.tagIntersection = intersection;
    this.onUpdateTags();
  }

  public onChooseMode(intersected = true): void {
    this.tagIntersection = intersected;
    this.dispatchState();
    this.chooseMode.emit(intersected);
  }

  public onUpdateTags(): void {
    this.updateTagsLists.next({selected: this.selectedTags, deselected: this.deselectedTags});
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
    this.tags.forEach((tag: string) => {
      this.filtersButtonsState[tag] = 0;
    });

    this.onUpdateTags();
    this.dispatchState();
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
    this.dispatchState();
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
    this.dispatchState();
  }

  private dispatchState(): void {
    this.store.dispatch(
      setFamilyTags({
        selectedFamilyTags: cloneDeep(this.selectedTags),
        deselectedFamilyTags: cloneDeep(this.deselectedTags),
        tagIntersection: cloneDeep(this.tagIntersection),
      })
    );
  }
}
