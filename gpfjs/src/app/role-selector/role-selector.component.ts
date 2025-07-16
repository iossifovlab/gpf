import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { MeasuresService } from 'app/measures/measures.service';
import { distinctUntilChanged, Subject, switchMap, take } from 'rxjs';

@Component({
    selector: 'gpf-role-selector',
    templateUrl: './role-selector.component.html',
    styleUrl: './role-selector.component.css',
    standalone: false
})
export class RoleSelectorComponent implements OnInit {
  @Input() public initialState: string[] = [];
  @Output() public updateSelectedRoles = new EventEmitter<string[]>();
  public roleSuggestions = [];
  public searchValue = '';
  public searchBoxInput$: Subject<string> = new Subject();
  public roles: string[] = [];
  public selectedRoles: string[] = [];

  public constructor(private measuresService: MeasuresService, private store: Store) {}

  public ngOnInit(): void {
    this.store.select(selectDatasetId).pipe(
      take(1),
      switchMap(datasetIdState => this.measuresService.getMeasureRoles(datasetIdState)),
    ).subscribe(roles => {
      this.roles = roles;
      this.roleSuggestions = this.roles;
      if (this.initialState) {
        this.selectedRoles = this.initialState;
      }
    });

    this.searchBoxInput$.pipe(distinctUntilChanged()).subscribe(() => {
      if (!this.searchValue) {
        this.roleSuggestions = this.roles;
        return;
      }
      this.filterSuggestions();
    });
  }

  public filterSuggestions(): void {
    this.roleSuggestions = this.roles.filter(role => {
      const roleLowerCase = role.toLowerCase();
      const searchValueLowerCase = this.searchValue.toLowerCase();
      return roleLowerCase.startsWith(searchValueLowerCase);
    });
  }

  public addToSelected(role: string): void {
    if (!this.roleSuggestions.includes(role)) {
      this.searchValue = '';
      return;
    }
    if (!this.selectedRoles.find(r => r === role)) {
      this.selectedRoles.push(role);
      this.updateSelectedRoles.emit(this.selectedRoles);
    }
    this.searchValue = '';
    this.searchBoxInput$.next(this.searchValue);
  }

  public removeFromSelected(role: string): void {
    const index = this.selectedRoles.findIndex(r => r === role);
    if (index > -1) {
      this.selectedRoles.splice(index, 1);
      this.updateSelectedRoles.emit(this.selectedRoles);
    }
  }

  public isSelected(role: string): boolean {
    return Boolean(this.selectedRoles.find(r => r === role));
  }
}
