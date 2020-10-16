/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { StudyTypesComponent } from './study-types.component';
import { StateRestoreService } from 'app/store/state-restore.service';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';

describe('StudyTypesComponent', () => {
  let component: StudyTypesComponent;
  let fixture: ComponentFixture<StudyTypesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [StudyTypesComponent, ErrorsAlertComponent],
      providers: [StateRestoreService]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(StudyTypesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
