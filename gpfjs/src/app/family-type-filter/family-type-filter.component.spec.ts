import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CheckboxListComponent, DisplayNamePipe } from 'app/checkbox-list/checkbox-list.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { FamilyTypeFilterComponent } from './family-type-filter.component';
import { StoreModule } from '@ngrx/store';

describe('FamilyTypeFilterComponent', () => {
  let component: FamilyTypeFilterComponent;
  let fixture: ComponentFixture<FamilyTypeFilterComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [FamilyTypeFilterComponent, CheckboxListComponent, ErrorsAlertComponent, DisplayNamePipe],
      imports: [StoreModule.forRoot({})]
    }).compileComponents();

    fixture = TestBed.createComponent(FamilyTypeFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });
  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
