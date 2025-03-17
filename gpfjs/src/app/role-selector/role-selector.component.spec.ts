import { ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';

import { RoleSelectorComponent } from './role-selector.component';
import { MatAutocompleteOrigin, MatAutocomplete, MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { MeasuresService } from 'app/measures/measures.service';
import { provideHttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { StoreModule } from '@ngrx/store';
import { datasetIdReducer } from 'app/datasets/datasets.state';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { Observable, of } from 'rxjs';

class MeasuresServiceMock {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getMeasureRoles(datasetId: string): Observable<string[]> {
    return of(['mom', 'dad', 'prb']);
  }
}
describe('RoleSelectorComponent', () => {
  let component: RoleSelectorComponent;
  let fixture: ComponentFixture<RoleSelectorComponent>;
  const measuresServiceMock = new MeasuresServiceMock();

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [RoleSelectorComponent],
      imports: [
        MatAutocompleteOrigin,
        MatAutocomplete,
        MatAutocompleteTrigger,
        StoreModule.forRoot({datasetId: datasetIdReducer}),
      ],
      providers: [
        ConfigService,
        { provide: MeasuresService, useValue: measuresServiceMock },
        provideHttpClient(),
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(RoleSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load selected roles from state', () => {
    component.initialState = ['mom'];
    component.ngOnInit();
    expect(component.roles).toStrictEqual(['mom', 'dad', 'prb']);
    expect(component.roleSuggestions).toStrictEqual(['mom', 'dad', 'prb']);
    expect(component.selectedRoles).toStrictEqual(['mom']);
  });

  it('should trigger roles searching', fakeAsync(() => {
    const filterSpy = jest.spyOn(component, 'filterSuggestions');
    const mockSearchValue = 'mo';
    component.searchValue = mockSearchValue;

    component.searchBoxInput$.next(mockSearchValue);
    tick(100);
    expect(filterSpy).toHaveBeenCalledWith();
  }));

  it('should not trigger roles searching when search value is empty', fakeAsync(() => {
    const filterSpy = jest.spyOn(component, 'filterSuggestions');
    const mockSearchValue = '';
    component.searchValue = mockSearchValue;

    component.searchBoxInput$.next(mockSearchValue);
    tick(100);
    expect(component.roleSuggestions).toStrictEqual(['mom', 'dad', 'prb']);
    expect(filterSpy).not.toHaveBeenCalledWith();
  }));

  it('should filter role options based on searching value', () => {
    component.searchValue = 'mo';
    component.filterSuggestions();
    expect(component.roleSuggestions).toStrictEqual(['mom']);
  });

  it('should select role', () => {
    const updateSelectedRolesSpy = jest.spyOn(component.updateSelectedRoles, 'emit');
    const searchBoxInputSpy = jest.spyOn(component.searchBoxInput$, 'next');

    component.selectedRoles = [];
    component.searchValue = 'pr';
    component.addToSelected('prb');

    expect(component.selectedRoles).toStrictEqual(['prb']);
    expect(updateSelectedRolesSpy).toHaveBeenCalledWith(['prb']);
    expect(component.searchValue).toBe('');
    expect(searchBoxInputSpy).toHaveBeenCalledWith('');
  });

  it('should not select already selected role', () => {
    const updateSelectedRolesSpy = jest.spyOn(component.updateSelectedRoles, 'emit');
    const searchBoxInputSpy = jest.spyOn(component.searchBoxInput$, 'next');

    component.selectedRoles = ['prb'];
    component.searchValue = 'pr';
    component.addToSelected('prb');

    expect(component.selectedRoles).toStrictEqual(['prb']);
    expect(updateSelectedRolesSpy).not.toHaveBeenCalledWith();
    expect(component.searchValue).toBe('');
    expect(searchBoxInputSpy).toHaveBeenCalledWith('');
  });

  it('should remove selected role', () => {
    const updateSelectedRolesSpy = jest.spyOn(component.updateSelectedRoles, 'emit');

    component.selectedRoles = ['prb', 'dad'];
    component.removeFromSelected('prb');

    expect(component.selectedRoles).toStrictEqual(['dad']);
    expect(updateSelectedRolesSpy).not.toHaveBeenCalledWith();
  });

  it('should check if role is selected', () => {
    component.selectedRoles = ['prb'];
    expect(component.isSelected('prb')).toBe(true);
    expect(component.isSelected('dad')).toBe(false);
  });
});
