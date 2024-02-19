import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NgxsModule } from '@ngxs/store';
import { CheckboxListComponent, DisplayNamePipe } from 'app/checkbox-list/checkbox-list.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { FamilyTypeFilterComponent } from './family-type-filter.component';

describe('FamilyTypeFilterComponent', () => {
  let component: FamilyTypeFilterComponent;
  let fixture: ComponentFixture<FamilyTypeFilterComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [FamilyTypeFilterComponent, CheckboxListComponent, ErrorsAlertComponent, DisplayNamePipe],
      imports: [NgxsModule.forRoot([], {developmentMode: true})]
    }).compileComponents();

    fixture = TestBed.createComponent(FamilyTypeFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });
  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
