import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

@Component({
  selector: 'gpf-role-selector',
  templateUrl: './role-selector.component.html',
  styleUrl: './role-selector.component.css'
})
export class RoleSelectorComponent implements OnInit {
  @Input() public initialState: string[] = [];
  // @Input() public roles: string[];
  @Output() public updateSelectedRoles = new EventEmitter<string[]>();
  public roleSuggestions = [];
  public searchValue = '';
  public searchBoxInput$: Subject<string> = new Subject();
  public roles: string[] = [];
  public selectedRoles: string[] = [];

  public ngOnInit(): void {
    this.roles = ['all', 'mom', 'dad', 'proband'];

    if (this.initialState.length) {
      this.selectedRoles = this.roles.filter(r => this.initialState.includes(r));
    }

    this.searchBoxInput$.pipe(debounceTime(100), distinctUntilChanged()).subscribe(() => {
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
    if (!this.selectedRoles.find(r => r === role)) {
      if (role === 'all') {
        this.selectedRoles = [];
      }
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
    return this.selectedRoles.includes('all') ? true : Boolean(this.selectedRoles.find(r => r === role));
  }
}
