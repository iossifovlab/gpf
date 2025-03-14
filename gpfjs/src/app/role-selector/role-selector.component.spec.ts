import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RoleSelectorComponent } from './role-selector.component';
import { MatAutocompleteOrigin, MatAutocomplete, MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { MeasuresService } from 'app/measures/measures.service';
import { provideHttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { StoreModule } from '@ngrx/store';
import { datasetIdReducer } from 'app/datasets/datasets.state';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('RoleSelectorComponent', () => {
  let component: RoleSelectorComponent;
  let fixture: ComponentFixture<RoleSelectorComponent>;

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
        MeasuresService,
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
});
