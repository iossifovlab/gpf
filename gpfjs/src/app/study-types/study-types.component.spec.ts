/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { StudyTypesComponent } from './study-types.component';
import { StateRestoreService } from 'app/store/state-restore.service';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { of } from 'rxjs';

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

  it('should initialize', () => {
    const getStateSpy = spyOn(component['stateRestoreService'], 'getState');
    const selectNoneSpy = spyOn(component, 'selectNone').and.callThrough();

    getStateSpy.and.returnValue(of({studyTypes: undefined}));
    component.ngOnInit();
    expect(selectNoneSpy).toHaveBeenCalledTimes(0);

    getStateSpy.and.returnValue(of({studyTypes: ['we']}));
    component.ngOnInit();
    expect(selectNoneSpy).toHaveBeenCalledTimes(1);
    expect(component.studyTypes.we).toBeTrue();
    expect(component.studyTypes.tg).toBeFalse();
    expect(component.studyTypes.wg).toBeFalse();

    getStateSpy.and.returnValue(of({studyTypes: ['tg']}));
    component.ngOnInit();
    expect(selectNoneSpy).toHaveBeenCalledTimes(2);
    expect(component.studyTypes.we).toBeFalse();
    expect(component.studyTypes.tg).toBeTrue();
    expect(component.studyTypes.wg).toBeFalse();

    getStateSpy.and.returnValue(of({studyTypes: ['wg']}));
    component.ngOnInit();
    expect(selectNoneSpy).toHaveBeenCalledTimes(3);
    expect(component.studyTypes.we).toBeFalse();
    expect(component.studyTypes.tg).toBeFalse();
    expect(component.studyTypes.wg).toBeTrue();

    getStateSpy.and.returnValue(of({studyTypes: ['we', 'tg', 'wg']}));
    component.ngOnInit();
    expect(selectNoneSpy).toHaveBeenCalledTimes(4);
    expect(component.studyTypes.we).toBeTrue();
    expect(component.studyTypes.tg).toBeTrue();
    expect(component.studyTypes.wg).toBeTrue();
  });

  it('should select all', () => {
    component.studyTypes.tg = false;
    component.studyTypes.we = false;
    component.studyTypes.wg = false;

    component.selectAll();

    expect(component.studyTypes.we).toBeTrue();
    expect(component.studyTypes.tg).toBeTrue();
    expect(component.studyTypes.wg).toBeTrue();
  });

  it('should select none', () => {
    component.studyTypes.tg = true;
    component.studyTypes.we = true;
    component.studyTypes.wg = true;

    component.selectNone();

    expect(component.studyTypes.we).toBeFalse();
    expect(component.studyTypes.tg).toBeFalse();
    expect(component.studyTypes.wg).toBeFalse();
  });

  it('should check study types value', () => {
    component.selectNone();

    component.studyTypesCheckValue('abcd', true);
    expect(component.studyTypes.we).toBeFalse();
    expect(component.studyTypes.tg).toBeFalse();
    expect(component.studyTypes.wg).toBeFalse();

    component.studyTypesCheckValue('we', true);
    expect(component.studyTypes.we).toBeTrue();
    component.studyTypesCheckValue('we', false);
    expect(component.studyTypes.we).toBeFalse();

    component.studyTypesCheckValue('tg', true);
    expect(component.studyTypes.tg).toBeTrue();
    component.studyTypesCheckValue('tg', false);
    expect(component.studyTypes.tg).toBeFalse();

    component.studyTypesCheckValue('wg', true);
    expect(component.studyTypes.wg).toBeTrue();
    component.studyTypesCheckValue('wg', false);
    expect(component.studyTypes.wg).toBeFalse();
  });

  it('should get state', () => {
    component.studyTypes = {we: true, tg: true, wg: true};
    component.getState().take(1).subscribe(state => expect(state).toEqual({
      studyTypes: [ 'we', 'tg', 'wg' ]
    }));
  });
});
