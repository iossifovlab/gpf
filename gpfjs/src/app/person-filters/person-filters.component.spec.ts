import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgxsModule } from '@ngxs/store';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';

import { PersonFiltersComponent } from './person-filters.component';
import { PersonFiltersState } from './person-filters.state';

describe('PersonFiltersComponent', () => {
  let component: PersonFiltersComponent;
  let fixture: ComponentFixture<PersonFiltersComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PersonFiltersComponent, ErrorsAlertComponent],
      imports: [NgxsModule.forRoot([PersonFiltersState], {developmentMode: true})],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PersonFiltersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
