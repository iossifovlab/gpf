import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { UsersService } from 'app/users/users.service';
// tslint:disable-next-line:import-blacklist
import { Subject } from 'rxjs';
import { Gene } from './gene';

import { GeneViewComponent, GeneViewZoomHistory, GeneViewScaleState } from './gene-view.component';

describe('GeneViewScaleState', () => {
  it('should have working getters', () => {
    const testScaleState = new GeneViewScaleState([1, 10], 5, 15, false);
    expect(testScaleState.xMin).toBe(1);
    expect(testScaleState.xMax).toBe(10);
  });
});

describe('GeneViewZoomHistory', () => {
  it('should add state to history', () => {
    const testZoomHistory = new GeneViewZoomHistory();

    const testScaleState1 = new GeneViewScaleState([1, 10], 5, 15, false);
    testZoomHistory.addStateToHistory(testScaleState1);
    expect(testZoomHistory.currentState).toEqual(testScaleState1);

    const testScaleState2 = new GeneViewScaleState([10, 20], 5, 25, false);
    testZoomHistory.addStateToHistory(testScaleState2);
    expect(testZoomHistory.currentState).toEqual(testScaleState2);
  });

  it('should check if index can go forward and backward', () => {
    const testScaleState = new GeneViewScaleState([1, 10], 5, 15, false);
    const testZoomHistory = new GeneViewZoomHistory();
    testZoomHistory.addStateToHistory(testScaleState);
    expect(testZoomHistory.canGoBackward).toBe(false);
    expect(testZoomHistory.canGoForward).toBe(false);
    testZoomHistory.addStateToHistory(testScaleState);
    expect(testZoomHistory.canGoBackward).toBe(true);
    expect(testZoomHistory.canGoForward).toBe(false);
  });

  it('should reset to default state', () => {
    const testScaleState1 = new GeneViewScaleState([1, 10], 5, 15, false);
    const testScaleState2 = new GeneViewScaleState([10, 20], 5, 25, false);
    const testZoomHistory = new GeneViewZoomHistory();
    testZoomHistory.addStateToHistory(testScaleState1);
    testZoomHistory.addStateToHistory(testScaleState2);

    const testDefaultState = new GeneViewScaleState([0, 0], 0, 0, false);
    testZoomHistory.resetToDefaultState(testDefaultState);
    expect(testZoomHistory.currentState).toEqual(testDefaultState);
    expect(testZoomHistory.canGoBackward).toBe(false);
    expect(testZoomHistory.canGoForward).toBe(false);
  });

  it('should move to previous and next states', () => {
    const testScaleState1 = new GeneViewScaleState([1, 10], 5, 15, false);
    const testScaleState2 = new GeneViewScaleState([10, 20], 5, 25, false);
    const testZoomHistory = new GeneViewZoomHistory();
    testZoomHistory.addStateToHistory(testScaleState1);
    testZoomHistory.addStateToHistory(testScaleState2);

    testZoomHistory.moveToPrevious();
    expect(testZoomHistory.currentState).toEqual(testScaleState1);
    testZoomHistory.moveToNext();
    expect(testZoomHistory.currentState).toEqual(testScaleState2);
  });
});

describe('GeneViewComponent', () => {
  let component: GeneViewComponent;
  let fixture: ComponentFixture<GeneViewComponent>;

  const testGene = Gene.fromJson({
    'gene': 'testGene',
    'transcripts':
      [{
        'transcript_id': 'testTranscriptId1',
        'strand': 'testStrand1',
        'chrom': 'testChrom1',
        'cds': [1, 30],
        'exons': [{'start': 1, 'stop': 11}, {'start': 12, 'stop': 22}]
      }, {
        'transcript_id': 'testTranscriptId2',
        'strand': 'testStrand2',
        'chrom': 'testChrom2',
        'cds': [20, 50],
        'exons': [{'start': 23, 'stop': 33}, {'start': 34, 'stop': 44}]
      }]
  });
  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [GeneViewComponent],
      providers: [
        DatasetsService,
        UsersService,
        ConfigService,
        FullscreenLoadingService],
      imports: [HttpClientTestingModule, RouterTestingModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GeneViewComponent);
    component = fixture.componentInstance;
    component.streamingFinished$ = new Subject<boolean>();
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should enable and disable intro condensing', () => {
    component.enableIntronCondensing();
    expect(component.condenseIntrons).toBeTrue();
    component.disableIntronCondensing();
    expect(component.condenseIntrons).toBeFalse();
  });

  it('should redraw', () => {
    const drawGeneSpy = spyOn(component, 'drawGene');
    const drawPlotSpy = spyOn(component, 'drawPlot');

    component.redraw();
    expect(drawGeneSpy).not.toHaveBeenCalled();
    expect(drawPlotSpy).not.toHaveBeenCalled();

    component.gene = testGene;

    component.redraw();
    expect(drawGeneSpy).toHaveBeenCalled();
    expect(drawPlotSpy).toHaveBeenCalled();
  });

  it('should redraw and update table', () => {
    const redrawSpy = spyOn(component, 'redraw');
    const updateFamilyVariantsTableSpy = spyOn(component, 'updateFamilyVariantsTable');

    component.redrawAndUpdateTable();
    expect(redrawSpy).toHaveBeenCalled();
    expect(updateFamilyVariantsTableSpy).toHaveBeenCalled();
  });

  it('should check Show Denovo and redraw', () => {
    const redrawAndUpdateTableSpy = spyOn(component, 'redrawAndUpdateTable');
    component.showDenovo = false;

    component.checkShowDenovo(true);
    expect(component.showDenovo).toBeTrue();
    expect(redrawAndUpdateTableSpy).toHaveBeenCalled();
    component.checkShowDenovo(false);
    expect(component.showDenovo).toBeFalse();
    expect(redrawAndUpdateTableSpy).toHaveBeenCalled();
  });

  it('should check Show Transmitted and redraw', () => {
    const redrawAndUpdateTableSpy = spyOn(component, 'redrawAndUpdateTable');
    component.showTransmitted = false;

    component.checkShowTransmitted(true);
    expect(component.showTransmitted).toBeTrue();
    expect(redrawAndUpdateTableSpy).toHaveBeenCalled();
    component.checkShowTransmitted(false);
    expect(component.showTransmitted).toBeFalse();
    expect(redrawAndUpdateTableSpy).toHaveBeenCalled();
  });

  it('should check Effect Type and redraw', () => {
    const redrawAndUpdateTableSpy = spyOn(component, 'redrawAndUpdateTable');
    expect(component.selectedEffectTypes.indexOf('lgds')).not.toBe(-1);

    component.checkEffectType('lgds', false);
    expect(component.selectedEffectTypes.indexOf('lgds')).toBe(-1);
    expect(redrawAndUpdateTableSpy).toHaveBeenCalled();
    component.checkEffectType('lgds', true);
    expect(component.selectedEffectTypes.indexOf('lgds')).not.toBe(-1);
    expect(redrawAndUpdateTableSpy).toHaveBeenCalled();
  });

  it('should check Affected Status and redraw', () => {
    const redrawAndUpdateTableSpy = spyOn(component, 'redrawAndUpdateTable');
    expect(component.selectedAffectedStatus.indexOf('Affected only')).not.toBe(-1);

    component.checkAffectedStatus('Affected only', false);
    expect(component.selectedAffectedStatus.indexOf('Affected only')).toBe(-1);
    expect(redrawAndUpdateTableSpy).toHaveBeenCalled();
    component.checkAffectedStatus('Affected only', true);
    expect(component.selectedAffectedStatus.indexOf('Affected only')).not.toBe(-1);
    expect(redrawAndUpdateTableSpy).toHaveBeenCalled();
  });

  it('should see if Affected Status is selected', () => {
    spyOn(component, 'redrawAndUpdateTable');
    component.checkAffectedStatus('Affected only', false);
    expect(component.isAffectedStatusSelected('Affected only')).toBeFalse();
    component.checkAffectedStatus('Affected only', true);
    expect(component.isAffectedStatusSelected('Affected only')).toBeTrue();
  });
});
