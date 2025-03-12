import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RoleSelectorComponent } from './role-selector.component';
import { MatAutocompleteOrigin, MatAutocomplete, MatAutocompleteTrigger } from '@angular/material/autocomplete';

describe('RoleSelectorComponent', () => {
  let component: RoleSelectorComponent;
  let fixture: ComponentFixture<RoleSelectorComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [RoleSelectorComponent],
      imports: [
        MatAutocompleteOrigin,
        MatAutocomplete,
        MatAutocompleteTrigger
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RoleSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
