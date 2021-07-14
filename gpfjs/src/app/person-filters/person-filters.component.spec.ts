import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NgxsModule } from '@ngxs/store';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';

import { PersonFiltersComponent } from './person-filters.component';

describe('PersonFiltersComponent', () => {
  let component: PersonFiltersComponent;
  let fixture: ComponentFixture<PersonFiltersComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PersonFiltersComponent, ErrorsAlertComponent ],
      imports: [NgxsModule.forRoot([])],
    })
    .compileComponents();
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
