import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { FamilyIdsComponent } from './family-ids.component';
import { familyIdsReducer } from './family-ids.state';
import { StoreModule } from '@ngrx/store';

describe('FamilyIdsComponent', () => {
  let component: FamilyIdsComponent;
  let fixture: ComponentFixture<FamilyIdsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [FamilyIdsComponent, ErrorsAlertComponent],
      imports: [FormsModule, StoreModule.forRoot({familyIds: familyIdsReducer})]
    }).compileComponents();

    fixture = TestBed.createComponent(FamilyIdsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
