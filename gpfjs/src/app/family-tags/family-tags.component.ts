import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { StatefulComponent } from 'app/common/stateful-component';
import { FamilyTagsState, SetFamilyTags } from './family-tags.state';
import { Store } from '@ngxs/store';
import { FamilyTags } from './family-tags';

@Component({
  selector: 'gpf-family-tags',
  templateUrl: './family-tags.component.html',
  styleUrls: ['./family-tags.component.css']
})
export class FamilyTagsComponent extends StatefulComponent implements OnInit {
  @Input() public numOfCols: number;
  @Input() public tags = [];
  @Output() public chooseMode = new EventEmitter<boolean>();
  @Output() public updateTagsLists = new EventEmitter();

  public selectedTags: string[] = [];
  public deselectedTags: string[] = [];
  public filtersButtonsState: Record<string, number> = {};
  public tagIntersection = true; // mode "And"
  public familyTags = new FamilyTags();

  public constructor(protected store: Store) {
    super(store, FamilyTagsState, 'familyTags');
  }

  public ngOnInit(): void {
    this.tags.forEach((tag: string) => {
      this.filtersButtonsState[tag] = 0;
    });

    this.store.selectOnce(state => state.familyTagsState).subscribe((state: SetFamilyTags) => {
      this.restoreFamilyTags(state.selectedFamilyTags, state.deselectedFamilyTags, state.tagIntersection);
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

    this.familyTags.deselectedTags = deselectedTags;
    this.familyTags.selectedTags = selectedTags;
    this.familyTags.tagIntersection = intersection;
    this.store.dispatch(new SetFamilyTags(this.selectedTags, this.deselectedTags, this.tagIntersection));
    this.onUpdateTags();
  }

  public onChooseMode(intersected = true): void {
    this.tagIntersection = intersected;
    this.store.dispatch(new SetFamilyTags(this.selectedTags, this.deselectedTags, this.tagIntersection));
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
    this.store.dispatch(new SetFamilyTags(this.selectedTags, this.deselectedTags, this.tagIntersection));
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
    this.store.dispatch(new SetFamilyTags(this.selectedTags, this.deselectedTags, this.tagIntersection));
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
    this.store.dispatch(new SetFamilyTags(this.selectedTags, this.deselectedTags, this.tagIntersection));
    this.onUpdateTags();
  }
}
