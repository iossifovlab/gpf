import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { personIdsReducer } from './person-ids.state';
import { ErrorsAlertComponent } from '../errors-alert/errors-alert.component';

import { PersonIdsComponent } from './person-ids.component';
import { StoreModule } from '@ngrx/store';

describe('PersonIdsComponent', () => {
  let component: PersonIdsComponent;
  let fixture: ComponentFixture<PersonIdsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PersonIdsComponent, ErrorsAlertComponent],
      imports: [FormsModule, StoreModule.forRoot({personIds: personIdsReducer})],
    }).compileComponents();

    fixture = TestBed.createComponent(PersonIdsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
