import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { RARITY_ALL, RARITY_INTERVAL, RARITY_RARE, RARITY_ULTRARARE } from './present-in-parent';

import { PresentInParentComponent } from './present-in-parent.component';

describe('PresentInParentComponent', () => {
  let component: PresentInParentComponent;
  let fixture: ComponentFixture<PresentInParentComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PresentInParentComponent ],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PresentInParentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should restore checked state', () => {
    expect(component.presentInParent.motherOnly).toBeFalse();
    expect(component.presentInParent.fatherOnly).toBeFalse();
    expect(component.presentInParent.motherFather).toBeFalse();
    expect(component.presentInParent.neither).toBeTrue();

    component.restoreCheckedState(['father only']);
    expect(component.presentInParent.motherOnly).toBeFalse();
    expect(component.presentInParent.fatherOnly).toBeTrue();
    expect(component.presentInParent.motherFather).toBeFalse();
    expect(component.presentInParent.neither).toBeTrue();

    component.restoreCheckedState(['mother only']);
    expect(component.presentInParent.motherOnly).toBeTrue();
    expect(component.presentInParent.fatherOnly).toBeTrue();
    expect(component.presentInParent.motherFather).toBeFalse();
    expect(component.presentInParent.neither).toBeTrue();

    component.restoreCheckedState(['mother and father']);
    expect(component.presentInParent.motherOnly).toBeTrue();
    expect(component.presentInParent.fatherOnly).toBeTrue();
    expect(component.presentInParent.motherFather).toBeTrue();
    expect(component.presentInParent.neither).toBeTrue();
  });


  it('should restore rarity', () => {
    const resetRarity = () => {
      component.presentInParent.ultraRare = undefined;
      component.presentInParent.rarityType = undefined;
      component.presentInParent.rarityIntervalStart = undefined;
      component.presentInParent.rarityIntervalEnd = undefined;
    };
    resetRarity();
    const restoreRadioButtonStateSpy = spyOn(component, 'restoreRadioButtonState');

    component.restoreRarity({ultraRare: true});
    expect(component.presentInParent.ultraRare).toEqual(true);
    expect(component.presentInParent.rarityType).toEqual(RARITY_ULTRARARE);
    expect(component.presentInParent.rarityIntervalStart).toEqual(undefined);
    expect(component.presentInParent.rarityIntervalEnd).toEqual(undefined);
    expect(restoreRadioButtonStateSpy).toHaveBeenCalledTimes(0);
    resetRarity();

    component.restoreRarity({minFreq: 'fakeMinFreqNumber'});
    expect(component.presentInParent.ultraRare).toEqual(false);
    expect(component.presentInParent.rarityType).toEqual(undefined);
    expect(component.presentInParent.rarityIntervalStart).toEqual('fakeMinFreqNumber' as any);
    expect(component.presentInParent.rarityIntervalEnd).toEqual(undefined);
    expect(restoreRadioButtonStateSpy).toHaveBeenCalledTimes(1);
    resetRarity();

    component.restoreRarity({maxFreq: 'fakeMaxFreqNumber'});
    expect(component.presentInParent.ultraRare).toEqual(false);
    expect(component.presentInParent.rarityType).toEqual(undefined);
    expect(component.presentInParent.rarityIntervalStart).toEqual(undefined);
    expect(component.presentInParent.rarityIntervalEnd).toEqual('fakeMaxFreqNumber' as any);
    expect(restoreRadioButtonStateSpy).toHaveBeenCalledTimes(2);
    resetRarity();

    component.restoreRarity({minFreq: 'fakeMinFreqNumber', maxFreq: 'fakeMaxFreqNumber'});
    expect(component.presentInParent.ultraRare).toEqual(false);
    expect(component.presentInParent.rarityType).toEqual(undefined);
    expect(component.presentInParent.rarityIntervalStart).toEqual('fakeMinFreqNumber' as any);
    expect(component.presentInParent.rarityIntervalEnd).toEqual('fakeMaxFreqNumber' as any);
    expect(restoreRadioButtonStateSpy).toHaveBeenCalledTimes(3);

    expect(restoreRadioButtonStateSpy.calls.allArgs()).toEqual([
      [{minFreq: 'fakeMinFreqNumber'}],
      [{maxFreq: 'fakeMaxFreqNumber'}],
      [{minFreq: 'fakeMinFreqNumber', maxFreq: 'fakeMaxFreqNumber'}],
    ]);
  });

  it('should restore radio button state', () => {
    const setFrequenciesStateSpy = spyOn(component, 'setFrequenciesState');
    component.restoreRadioButtonState({
      ultraRare: 'fakeUltraRareBoolean',
      minFreq: 'fakeMinFreqNumber',
      maxFreq: 'fakeMaxFreqNumber'
    });
    expect(setFrequenciesStateSpy.calls.allArgs()).toEqual([
      ['fakeUltraRareBoolean', 'fakeMinFreqNumber', 'fakeMaxFreqNumber']
    ]);
  });

  it('should set frequencies state', () => {
    const ultraRareValueChangeSpy = spyOn(component, 'ultraRareValueChange');
    const rarityTypeChangeSpy = spyOn(component, 'rarityTypeChange');

    component.setFrequenciesState(true, undefined, undefined);
    expect(ultraRareValueChangeSpy.calls.allArgs()).toEqual([[true]]);
    expect(rarityTypeChangeSpy).not.toHaveBeenCalled();

    component.setFrequenciesState(false, 1, undefined);
    expect(ultraRareValueChangeSpy.calls.allArgs()).toEqual([[true]]);
    expect(rarityTypeChangeSpy.calls.allArgs()).toEqual([[RARITY_INTERVAL]]);

    component.setFrequenciesState(false, -1, undefined);
    expect(ultraRareValueChangeSpy.calls.allArgs()).toEqual([[true]]);
    expect(rarityTypeChangeSpy.calls.allArgs()).toEqual([[RARITY_INTERVAL], [RARITY_ALL]]);

    component.setFrequenciesState(false, -1, 1);
    expect(ultraRareValueChangeSpy.calls.allArgs()).toEqual([[true]]);
    expect(rarityTypeChangeSpy.calls.allArgs()).toEqual([[RARITY_INTERVAL], [RARITY_ALL], [RARITY_RARE]]);
  });

  it('should restore state', () => {
    const getStateSpy = spyOn(component['stateRestoreService'], 'getState');
    const restoreCheckedStateSpy = spyOn(component, 'restoreCheckedState');
    const restoreRaritySpy = spyOn(component, 'restoreRarity');

    getStateSpy.and.returnValue(of({}));
    component.restoreState();
    expect(restoreCheckedStateSpy).not.toHaveBeenCalled();
    expect(restoreRaritySpy).not.toHaveBeenCalled();

    getStateSpy.and.returnValue(of({
      presentInParent: {
        presentInParent: 'mockPresentInParent1'
      }
    }));
    component.restoreState();
    expect(restoreCheckedStateSpy.calls.allArgs()).toEqual([['mockPresentInParent1']]);
    expect(restoreRaritySpy).not.toHaveBeenCalled();

    getStateSpy.and.returnValue(of({
      presentInParent: {
        rarity: 'mockRarity1'
      }
    }));
    component.restoreState();
    expect(restoreCheckedStateSpy.calls.allArgs()).toEqual([['mockPresentInParent1']]);
    expect(restoreRaritySpy.calls.allArgs()).toEqual([['mockRarity1']]);


    getStateSpy.and.returnValue(of({
      presentInParent: {
        presentInParent: 'mockPresentInParent2',
        rarity: 'mockRarity2'
      }
    }));
    component.restoreState();
    expect(restoreCheckedStateSpy.calls.allArgs()).toEqual([['mockPresentInParent1'], ['mockPresentInParent2']]);
    expect(restoreRaritySpy.calls.allArgs()).toEqual([['mockRarity1'], ['mockRarity2']]);
  });

  it('should restore state on init', () => {
    const restoreStateSpy = spyOn(component, 'restoreState');
    component.ngOnInit();
    expect(restoreStateSpy).toHaveBeenCalledTimes(1);
  });

  it('should select all', () => {
    component.presentInParent.fatherOnly = undefined;
    component.presentInParent.motherOnly = undefined;
    component.presentInParent.motherFather = undefined;
    component.presentInParent.neither = undefined;

    component.selectAll();
    expect(component.presentInParent.fatherOnly).toBeTrue();
    expect(component.presentInParent.motherOnly).toBeTrue();
    expect(component.presentInParent.motherFather).toBeTrue();
    expect(component.presentInParent.neither).toBeTrue();
  });

  it('should select none', () => {
    component.presentInParent.fatherOnly = undefined;
    component.presentInParent.motherOnly = undefined;
    component.presentInParent.motherFather = undefined;
    component.presentInParent.neither = undefined;

    component.selectNone();
    expect(component.presentInParent.fatherOnly).toBeFalse();
    expect(component.presentInParent.motherOnly).toBeFalse();
    expect(component.presentInParent.motherFather).toBeFalse();
    expect(component.presentInParent.neither).toBeFalse();
  });

  it('should check value in child', () => {
    component.presentInParent.fatherOnly = undefined;
    component.presentInParent.motherOnly = undefined;
    component.presentInParent.motherFather = undefined;
    component.presentInParent.neither = undefined;

    component.presentInChildCheckValue('fatherOnly', true);
    expect(component.presentInParent.fatherOnly).toBeTrue();
    component.presentInChildCheckValue('fatherOnly', false);
    expect(component.presentInParent.fatherOnly).toBeFalse();

    component.presentInChildCheckValue('motherOnly', true);
    expect(component.presentInParent.motherOnly).toBeTrue();
    component.presentInChildCheckValue('motherOnly', false);
    expect(component.presentInParent.motherOnly).toBeFalse();

    component.presentInChildCheckValue('motherFather', true);
    expect(component.presentInParent.motherFather).toBeTrue();
    component.presentInChildCheckValue('motherFather', false);
    expect(component.presentInParent.motherFather).toBeFalse();

    component.presentInChildCheckValue('neither', true);
    expect(component.presentInParent.neither).toBeTrue();
    component.presentInChildCheckValue('neither', false);
    expect(component.presentInParent.neither).toBeFalse();
  });

  it('should change value of rarity', () => {
    component.rarityChangeValue(2, 1024);
    expect(component.presentInParent.rarityIntervalStart).toEqual(2);
    expect(component.presentInParent.rarityIntervalEnd).toEqual(1024);
    component.rarityChangeValue(5, 13);
    expect(component.presentInParent.rarityIntervalStart).toEqual(5);
    expect(component.presentInParent.rarityIntervalEnd).toEqual(13);
  });

  it('should change type of rarity', () => {
    component.rarityTypeChange('fakeRarity');
    expect(component.presentInParent.rarityType).toEqual('fakeRarity');
  });

  it('should change value of ultra rare', () => {
    component.presentInParent.ultraRare = undefined;
    component.presentInParent.rarityType = undefined;

    component.ultraRareValueChange(false);
    expect(component.presentInParent.ultraRare).toEqual(false);
    expect(component.presentInParent.rarityType).toEqual(undefined);

    component.ultraRareValueChange(true);
    expect(component.presentInParent.ultraRare).toEqual(true);
    expect(component.presentInParent.rarityType).toEqual(RARITY_ULTRARARE);
  });

  it('should change radio rarity', () => {
    const ultraRareValueChangeSpy = spyOn(component, 'ultraRareValueChange');
    const rarityTypeChangeSpy = spyOn(component, 'rarityTypeChange');
    const rarityChangeValueSpy = spyOn(component, 'rarityChangeValue');
    const consoleLogSpy = spyOn(console, 'log');

    component.rarityRadioChange('all');
    expect(rarityTypeChangeSpy.calls.allArgs()).toEqual([[RARITY_ALL]]);
    expect(rarityChangeValueSpy.calls.allArgs()).toEqual([[0, 100]]);
    expect(consoleLogSpy).not.toHaveBeenCalled();

    component.rarityRadioChange('rare');
    expect(rarityTypeChangeSpy.calls.allArgs()).toEqual([[RARITY_ALL], [RARITY_RARE]]);
    expect(rarityChangeValueSpy.calls.allArgs()).toEqual([[0, 100], [0, 1]]);
    expect(consoleLogSpy).not.toHaveBeenCalled();

    component.rarityRadioChange('interval');
    expect(rarityTypeChangeSpy.calls.allArgs()).toEqual([[RARITY_ALL], [RARITY_RARE], [RARITY_INTERVAL]]);
    expect(rarityChangeValueSpy.calls.allArgs()).toEqual([[0, 100], [0, 1], [0, 1]]);
    expect(consoleLogSpy).not.toHaveBeenCalled();

    component.rarityRadioChange('abcd');
    expect(rarityTypeChangeSpy.calls.allArgs()).toEqual([[RARITY_ALL], [RARITY_RARE], [RARITY_INTERVAL]]);
    expect(rarityChangeValueSpy.calls.allArgs()).toEqual([[0, 100], [0, 1], [0, 1]]);
    expect(consoleLogSpy.calls.allArgs()).toEqual([['unexpected rarity: ', 'abcd']]);
  });

  it('should get state', () => {
    component.presentInParent = {
      motherOnly: false,
      fatherOnly: true,
      motherFather: false,
      neither: false,
      ultraRare: false,
      rarityIntervalStart: 2,
      rarityIntervalEnd: 16,
      rarityType: RARITY_INTERVAL
    };
    component.getState().take(1).subscribe(state =>
      expect(state).toEqual({
        presentInParent: {
          presentInParent: ['father only'],
          rarity: { ultraRare: null, minFreq: 2, maxFreq: 16 }
        }
      })
    );

    component.presentInParent = {
      motherOnly: true,
      fatherOnly: true,
      motherFather: true,
      neither: false,
      ultraRare: true,
      rarityIntervalStart: 2,
      rarityIntervalEnd: 16,
      rarityType: RARITY_ULTRARARE
    };
    component.getState().take(1).subscribe(state =>
      expect(state).toEqual({
        presentInParent: {
          presentInParent: ['father only', 'mother only', 'mother and father'],
          rarity: { ultraRare: true, minFreq: null, maxFreq: null }
        }
      })
    );

    component.presentInParent = {
      motherOnly: false,
      fatherOnly: false,
      motherFather: false,
      neither: true,
      ultraRare: false,
      rarityIntervalStart: -1,
      rarityIntervalEnd: null,
      rarityType: RARITY_ALL
    };
    component.getState().take(1).subscribe(state =>
      expect(state).toEqual({
        presentInParent: {
          presentInParent: ['neither'],
          rarity: { ultraRare: null, minFreq: null, maxFreq: null }
        }
      })
    );
  });
});
