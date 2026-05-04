import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { StudyTypesComponent } from './study-types.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { of } from 'rxjs';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { Store, StoreModule } from '@ngrx/store';
import { setStudyTypes, studyTypesReducer } from './study-types.state';

describe('StudyTypesComponent', () => {
  let component: StudyTypesComponent;
  let fixture: ComponentFixture<StudyTypesComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [StudyTypesComponent, ErrorsAlertComponent],
      providers: [],
      imports: [StoreModule.forRoot({studyTypes: studyTypesReducer})],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(StudyTypesComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of(['value1', 'value2']));

    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should restore state on initialization', () => {
    component.ngOnInit();
    expect(component.selectedValues).toStrictEqual(new Set(['value1', 'value2']));
  });

  it('should update variant types', () => {
    component.selectedValues = undefined;
    component['store'] = { dispatch() {} } as any;

    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    const mockSet = new Set(['value1', 'value2', 'value3']);

    component.updateStudyTypes(mockSet);

    expect(component.selectedValues).toStrictEqual(mockSet);
    expect(dispatchSpy).toHaveBeenNthCalledWith(1, setStudyTypes({studyTypes: [...mockSet]}));
  });
});
