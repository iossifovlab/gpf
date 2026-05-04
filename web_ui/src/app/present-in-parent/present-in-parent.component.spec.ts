import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { of } from 'rxjs';
import { PresentInParentComponent } from './present-in-parent.component';
import { presentInParentReducer, setPresentInParent } from './present-in-parent.state';
import { Store, StoreModule } from '@ngrx/store';
import { resetErrors, setErrors } from 'app/common/errors.state';

describe('PresentInParentComponent', () => {
  let component: PresentInParentComponent;
  let fixture: ComponentFixture<PresentInParentComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PresentInParentComponent],
      imports: [StoreModule.forRoot({presentInParent: presentInParentReducer})],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();
    fixture = TestBed.createComponent(PresentInParentComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);

    jest.spyOn(store, 'select').mockReturnValue(of({
      presentInParent: ['value1', 'value2'],
      rarity: {
        rarityType: 'rarityType',
        rarityIntervalStart: -12,
        rarityIntervalEnd: -11,
      }
    }));

    jest.spyOn(store, 'dispatch').mockImplementation();
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should restore state on init', () => {
    component.ngOnInit();
    expect(component.selectedValues).toStrictEqual(new Set(['value1', 'value2']));
    expect(component.selectedRarityType).toBe('rarityType');
    expect(component.rarityIntervalStart).toBe(-12);
    expect(component.rarityIntervalEnd).toBe(-11);
  });

  it('should update rarity interval start', () => {
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    const updateStateSpy = jest.spyOn(component, 'updateState');

    component.updateRarityIntervalStart(6);
    expect(component.rarityIntervalStart).toBe(6);
    expect(component.rarityIntervalEnd).toBeUndefined();
    expect(updateStateSpy).toHaveBeenCalledWith();
  });

  it('should update rarity interval end', () => {
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    const updateStateSpy = jest.spyOn(component, 'updateState');

    component.updateRarityIntervalEnd(100);
    expect(component.rarityIntervalEnd).toBe(100);
    expect(component.rarityIntervalStart).toBeUndefined();
    expect(updateStateSpy).toHaveBeenCalledWith();
  });

  it('should update rarity type', () => {
    component.rarityIntervalStart = 0;
    component.rarityIntervalEnd = 2;
    const updateStateSpy = jest.spyOn(component, 'updateState');

    component.updateRarityType('rare');
    expect(component.selectedRarityType).toBe('rare');
    expect(component.rarityIntervalStart).toBe(0);
    expect(component.rarityIntervalEnd).toBe(1);
    expect(updateStateSpy).toHaveBeenCalledTimes(1);

    component.updateRarityIntervalStart(1.23);
    expect(updateStateSpy).toHaveBeenCalledTimes(2);

    component.updateRarityType('ultraRare');
    expect(component.selectedRarityType).toBe('ultraRare');
    expect(component.rarityIntervalStart).toBe(0);
    expect(component.rarityIntervalEnd).toBe(1);
    expect(updateStateSpy).toHaveBeenCalledTimes(3);
  });

  it('should set default rarity type and intervals when no values were selected', () => {
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    component.selectedValues = null;
    component.selectedRarityType = '';
    const updateStateSpy = jest.spyOn(component, 'updateState');

    component.updatePresentInParent(new Set<string>([]));
    expect(component.rarityIntervalStart).toBe(0);
    expect(component.rarityIntervalEnd).toBe(1);
    expect(component.selectedRarityType).toBe('ultraRare');
    expect(updateStateSpy).toHaveBeenCalledWith();
  });

  it('should not set rarity type when selecting "neither"', () => {
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    component.selectedValues = null;
    component.selectedRarityType = '';
    const updateStateSpy = jest.spyOn(component, 'updateState');

    component.updatePresentInParent(new Set(['neither']));
    expect(component.rarityIntervalStart).toBeUndefined();
    expect(component.rarityIntervalEnd).toBeUndefined();
    expect(component.selectedRarityType).toBe('');
    expect(updateStateSpy).toHaveBeenCalledWith();
  });

  it('should set default rarity type when selecting more than one values', () => {
    component.rarityIntervalStart = undefined;
    component.rarityIntervalEnd = undefined;
    component.selectedValues = null;
    component.selectedRarityType = '';
    const updateStateSpy = jest.spyOn(component, 'updateState');

    component.updatePresentInParent(new Set(['father only', 'neither']));
    expect(component.rarityIntervalStart).toBeUndefined();
    expect(component.rarityIntervalEnd).toBeUndefined();
    expect(component.selectedRarityType).toBe('ultraRare');
    expect(updateStateSpy).toHaveBeenCalledWith();
  });

  it('should update state', () => {
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');

    component.updateState();
    expect(dispatchSpy).toHaveBeenCalledWith(setPresentInParent({
      presentInParent: {
        presentInParent: ['value1', 'value2'],
        rarity: {
          rarityType: 'rarityType',
          rarityIntervalStart: -12,
          rarityIntervalEnd: -11
        }
      }
    }));
  });

  it('should show error when rarity interval start and end are less than 0', () => {
    component.selectedRarityType = 'interval';
    component.rarityIntervalEnd = -1;

    component.updateRarityIntervalStart(-3);
    expect(component.errors).toStrictEqual([
      'rarityIntervalStart must not be less than 0',
      'rarityIntervalEnd must not be less than 0'
    ]);
  });

  it('should show error when rarity interval start and end are more than 100', () => {
    component.selectedRarityType = 'interval';
    component.rarityIntervalEnd = 300;

    component.updateRarityIntervalStart(200);
    expect(component.errors).toStrictEqual([
      'rarityIntervalStart must not be greater than 100',
      'rarityIntervalEnd must not be greater than 100'
    ]);
  });

  it('should show error when rarity interval start is more than interval end', () => {
    component.selectedRarityType = 'interval';
    component.rarityIntervalEnd = 10;

    component.updateRarityIntervalStart(20);
    expect(component.errors).toStrictEqual([
      'rarityIntervalStart should be less than or equal to rarityIntervalEnd',
      'rarityIntervalEnd should be more than or equal to rarityIntervalStart'
    ]);
  });

  it('should show error when rarity type is rare and end interval is less than 0', () => {
    component.selectedRarityType = 'rare';

    component.updateRarityIntervalEnd(-1);
    expect(component.errors).toStrictEqual([
      'rarityIntervalEnd must not be less than 0'
    ]);
  });

  it('should show error when rarity type is rare and end interval is more than 100', () => {
    component.selectedRarityType = 'rare';

    component.updateRarityIntervalEnd(200);
    expect(component.errors).toStrictEqual([
      'rarityIntervalEnd must not be greater than 100'
    ]);
  });

  it('should dispatch error messages to state', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.selectedRarityType = 'rare';

    component.updateRarityIntervalEnd(200);
    expect(dispatchSpy).toHaveBeenCalledWith(
      setErrors({
        errors: {
          componentId: 'presentInParent', errors: ['rarityIntervalEnd must not be greater than 100']
        }
      })
    );
  });

  it('should clean error messages from state when there are no errors', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.selectedRarityType = 'rare';

    component.updateRarityIntervalEnd(1);
    expect(dispatchSpy).toHaveBeenCalledWith(
      resetErrors({componentId: 'presentInParent'})
    );
  });
});
