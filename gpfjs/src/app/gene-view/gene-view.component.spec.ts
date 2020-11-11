import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { UsersService } from 'app/users/users.service';
import * as svgDrawing from 'app/utils/svg-drawing';
import * as d3 from 'd3';
// tslint:disable-next-line:import-blacklist
import { Subject, Observable } from 'rxjs';
import { DomainRange, Gene, GeneViewSummaryVariant, GeneViewSummaryVariantsArray } from './gene';
import { GeneViewModel } from './gene-view';

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

  beforeEach(() => {
    component.gene = testGene;
    component.streamingFinished$ = new Subject<boolean>();
    component.geneViewModel = new GeneViewModel(component.gene, component.svgWidth);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get current state', (done) => {
    component.zoomHistory.resetToDefaultState(new GeneViewScaleState([1, 10], 1, 10, false));
    component.x = {'_domain': [1, 10], domain() {return this._domain; }};
    const resolveRegionChromosomesSpy = spyOn(component.geneViewModel.collapsedGeneViewTranscript, 'resolveRegionChromosomes')
      .and.returnValue(['regions']);

    const state = component.getState();
    expect(resolveRegionChromosomesSpy).toHaveBeenCalled();
    const expectedState = {
      'affectedStatus': Array.from(component.selectedAffectedStatus),
      'selectedEffectTypes': Array.from(component.selectedEffectTypes),
      'zoomState': component.zoomHistory.currentState,
      'showDenovo': component.showDenovo,
      'showTransmitted': component.showTransmitted,
      'regions': ['regions']
    };

    state.subscribe(result => {
      expect(result).toEqual(expectedState);
      done();
    });
  });

  it('should enable and disable intro condensing', () => {
    component.enableIntronCondensing();
    expect(component.condenseIntrons).toBeTrue();
    component.disableIntronCondensing();
    expect(component.condenseIntrons).toBeFalse();
  });

  it('should draw transmitted icons with correct shapes and titles', () => {
    const drawTypes: any = ['drawStar', 'drawTriangle', 'drawCircle', 'drawDot'];
    const iconTitles = ['LGDs', 'Missense', 'Synonymous', 'Other'];

    const drawSpies = [];
    drawTypes.forEach((drawType, index) => {
      drawSpies[index] = spyOn(svgDrawing, drawType).and.callFake((element, x, y, color, title) => {
        expect(element).toEqual(component.svgElement);
        expect(title).toEqual(iconTitles[index]);
      });
    });

    component.drawTransmittedIcons();

    for (const drawSpy of drawSpies) {
      expect(drawSpy).toHaveBeenCalled();
    }
  });

  it('should draw denovo icons with correct shapes and titles', () => {
    const drawTypes: any = ['drawStar', 'drawTriangle', 'drawCircle', 'drawDot'];
    const iconTitles = ['Denovo LGDs', 'Denovo Missense', 'Denovo Synonymous', 'Denovo Other'];

    const drawSurroundingSquareSpy = spyOn(svgDrawing, 'drawSurroundingSquare');
    const drawSpies = [];
    drawTypes.forEach((drawType, index) => {
      drawSpies[index] = spyOn(svgDrawing, drawType).and.callFake((element, x, y, color, title) => {
        expect(element).toEqual(component.svgElement);
        expect(title).toEqual(iconTitles[index]);
      });
    });

    component.drawDenovoIcons();

    for (const drawSpy of drawSpies) {
      expect(drawSpy).toHaveBeenCalled();
    }
    expect(drawSurroundingSquareSpy).toHaveBeenCalledTimes(4);
  });

  it('should draw effect types icons with correct shapes and titles', () => {
    const drawTypes: any = ['drawStar', 'drawTriangle', 'drawCircle', 'drawDot'];
    const iconTitles = ['#LGDs', '#Missense', '#Synonymous', '#Other'];

    const drawSpies = [];
    drawTypes.forEach((drawType, index) => {
      drawSpies[index] = spyOn(svgDrawing, drawType).and.callFake((element, x, y, color, title) => {
        expect(element).toEqual(component.svgElement);
        expect(title).toEqual(iconTitles[index]);
      });
    });

    component.drawEffectTypesIcons();

    for (const drawSpy of drawSpies) {
      expect(drawSpy).toHaveBeenCalled();
    }
  });

  it('should set svg scale', () => {
    const calculateTextFontSizeSpy = spyOn(component, 'calculateTextFontSize').and.returnValue(100);
    component.fontSize = 0;
    component.svgWidth = 0;

    component.setSvgScale(1920);
    expect(calculateTextFontSizeSpy).toHaveBeenCalled();
    expect(component.fontSize).toBe(100);
    expect(component.svgWidth).toBe(1920 - component.options.margin.left - component.options.margin.right);
  });

  it('should redraw', () => {
    const drawGeneSpy = spyOn(component, 'drawGene');
    const drawPlotSpy = spyOn(component, 'drawPlot');

    component.gene = undefined;
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

  it('should recalculate X range', () => {
    component.svgWidth = 0;
    const buildNormalIntronsRangeSpy = spyOn(component.geneViewModel, 'buildNormalIntronsRange')
      .withArgs(1, 100, 0)
      .and.returnValue([0, 10]);
    const buildCondensedIntronsRangeSpy = spyOn(component.geneViewModel, 'buildCondensedIntronsRange')
      .withArgs(1, 100, 0)
      .and.returnValue([10, 20]);

    component.condenseIntrons = false;
    let newRange = component.recalculateXRange(1, 100);
    expect(buildNormalIntronsRangeSpy).toHaveBeenCalled();
    expect(newRange).toEqual([0, 10]);

    component.condenseIntrons = true;
    newRange = component.recalculateXRange(1, 100);
    expect(buildCondensedIntronsRangeSpy).toHaveBeenCalled();
    expect(newRange).toEqual([10, 20]);
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

  it('should see if Variant Effect is selected', () => {
    component.selectedEffectTypes = ['missense', 'synonymous'];
    expect(component.isVariantEffectSelected('lgds')).toBeFalse();
    expect(component.isVariantEffectSelected('splice-site')).toBeFalse();

    component.selectedEffectTypes = ['lgds', 'missense', 'synonymous'];
    expect(component.isVariantEffectSelected('lgds')).toBeTrue();
    expect(component.isVariantEffectSelected('splice-site')).toBeTrue();
  });

  it('should see if frequency is selected', () => {
    component.selectedFrequencies = [0, 10];
    expect(component.frequencyIsSelected(5)).toBeTrue();
    expect(component.frequencyIsSelected(15)).toBeFalse();
  });

  // it('should toggle condense intron', () => {
  //   const domain = {'domain': [1, 10], range(range) { this.domain = range; }};
  //   component.x = {'_domain': domain, domain() { return this._domain; }};
  //   const isCondensed = component.condenseIntrons;

  //   component.toggleCondenseIntron();
  //   expect(isCondensed).toBe(!isCondensed);
  // });

  it('should get different colors for Affected Statuses', () => {
    const affectedColor = component.getAffectedStatusColor('Affected only');
    const unaffectedColor = component.getAffectedStatusColor('Unaffected only');
    const otherColor = component.getAffectedStatusColor('Other status');

    expect(affectedColor).not.toEqual(unaffectedColor);
    expect(affectedColor).not.toEqual(otherColor);
    expect(unaffectedColor).not.toEqual(otherColor);
  });

  it('should get a variant\'s Affected Status', () => {
    let testVariant = GeneViewSummaryVariant.fromRow({ seen_in_affected: true, seen_in_unaffected: true });
    expect(component.getVariantAffectedStatus(testVariant)).toBe('Affected and unaffected');

    testVariant = GeneViewSummaryVariant.fromRow({ seen_in_affected: true, seen_in_unaffected: false });
    expect(component.getVariantAffectedStatus(testVariant)).toBe('Affected only');

    testVariant = GeneViewSummaryVariant.fromRow({ seen_in_affected: false, seen_in_unaffected: true });
    expect(component.getVariantAffectedStatus(testVariant)).toBe('Unaffected only');
  });

  it('should see if Affected Status is selected', () => {
    spyOn(component, 'redrawAndUpdateTable');
    component.checkAffectedStatus('Affected only', false);
    expect(component.isAffectedStatusSelected('Affected only')).toBeFalse();
    component.checkAffectedStatus('Affected only', true);
    expect(component.isAffectedStatusSelected('Affected only')).toBeTrue();
  });

  // it('should filter summary variants array', () => {

  // });

  it('should get pedigree affected status', () => {
    let mockPedigreeData = [ {'label': 0, 'color': ''}, {'label': 1, 'color': '#ffffff'} ];
    expect(component.getPedigreeAffectedStatus(mockPedigreeData)).toBe('Unaffected only');

    mockPedigreeData = [ {'label': 0, 'color': ''}, {'label': 1, 'color': 'other'} ];
    expect(component.getPedigreeAffectedStatus(mockPedigreeData)).toBe('Affected only');

    mockPedigreeData = [ {'label': 1, 'color': '#ffffff'}, {'label': 1, 'color': 'other'} ];
    expect(component.getPedigreeAffectedStatus(mockPedigreeData)).toBe('Affected and unaffected');
  });

  it('should get variant Y', () => {
    component.frequencyDomainMin = 11;

    component.y = d3.scaleLog()
      .domain([component.frequencyDomainMin, component.frequencyDomainMax])
      .range([component.subdomainAxisY, 0]);

    component.y_subdomain = d3.scaleLinear()
      .domain([0, component.frequencyDomainMin])
      .range([component.zeroAxisY, component.subdomainAxisY]);

    component.y_zero = d3.scalePoint()
      .domain(['0'])
      .range([component.svgHeightFreq, component.zeroAxisY]);

    const yZeroSpy = spyOn(component, 'y_zero').and.returnValue(1);
    const ySubdomainSpy = spyOn(component, 'y_subdomain').and.returnValue(2);
    const ySpy = spyOn(component, 'y').and.returnValue(3);

    expect(component.getVariantY(0)).toBe(1);
    expect(yZeroSpy).toHaveBeenCalled();
    expect(component.getVariantY(10)).toBe(2);
    expect(ySubdomainSpy).toHaveBeenCalled();
    expect(component.getVariantY(20)).toBe(3);
    expect(ySpy).toHaveBeenCalled();
  });

  it('should convert brush point to frequency', () => {
    component.y = d3.scaleLog()
      .domain([0, 0])
      .range([0, 0]);
    component.y_subdomain = d3.scaleLinear()
      .domain([0, 0])
      .range([0, 10]);
    component.y_zero = d3.scaleLog()
      .domain([0])
      .range([0, 20]);

    const ySpy = spyOn(component.y, 'invert').and.returnValue(1);
    const ySubdomainSpy = spyOn(component.y_subdomain, 'invert').and.returnValue(2);

    expect(component.convertBrushPointToFrequency(5)).toBe(1);
    expect(ySpy).toHaveBeenCalled();
    expect(component.convertBrushPointToFrequency(15)).toBe(2);
    expect(ySubdomainSpy).toHaveBeenCalled();
  });

  it('should set default scale', () => {
    const defaultScale = new GeneViewScaleState(component.geneViewModel.domain, 0, component.frequencyDomainMax, component.condenseIntrons);

    const resetToDefaultSpy = spyOn(component.zoomHistory, 'resetToDefaultState')
      .and.callFake((scale) => { expect(scale).toEqual(defaultScale); });

    component.setDefaultScale();
    expect(resetToDefaultSpy).toHaveBeenCalled();
  });

  it('should reset gene table values', () => {
    component.geneTableStats = {
      geneSymbol: 'symbol',
      chromosome: 'chrom',
      totalFamilyVariants: 10,
      selectedFamilyVariants: 10,
      totalSummaryVariants: 10,
      selectedSummaryVariants: 10,
    };

    component.resetGeneTableValues();
    expect(component.geneTableStats).toEqual({
      geneSymbol: '',
      chromosome: '',
      totalFamilyVariants: 0,
      selectedFamilyVariants: 0,
      totalSummaryVariants: 0,
      selectedSummaryVariants: 0,
    });
  });

  it('should undo state history', () => {
    const moveToPreviousSpy = spyOn(component.zoomHistory, 'moveToPrevious');
    const drawFromHistorySpy = spyOn(component, 'drawFromHistory');

    component.historyUndo();
    expect(moveToPreviousSpy).toHaveBeenCalled();
    expect(drawFromHistorySpy).toHaveBeenCalled();
  });

  it('should redo state history', () => {
    const moveToNextSpy = spyOn(component.zoomHistory, 'moveToNext');
    const drawFromHistorySpy = spyOn(component, 'drawFromHistory');

    component.historyRedo();
    expect(moveToNextSpy).toHaveBeenCalled();
    expect(drawFromHistorySpy).toHaveBeenCalled();
  });

  it('should handle undo and redo keyboard events', () => {
    const historyUndoSpy = spyOn(component, 'historyUndo');
    const historyRedoSpy = spyOn(component, 'historyRedo');

    component.handleKeyboardEvent({ctrlKey: false, key: 'z'});
    expect(historyUndoSpy).not.toHaveBeenCalled();

    component.handleKeyboardEvent({ctrlKey: true, key: 'z'});
    expect(historyUndoSpy).toHaveBeenCalled();

    component.handleKeyboardEvent({ctrlKey: true, key: 'y'});
    expect(historyRedoSpy).toHaveBeenCalled();
  });

  it('should calculate text font size', () => {
    expect(component.calculateTextFontSize(1200)).toBe(12);
    expect(component.calculateTextFontSize(1650)).toBeGreaterThan(12);
    expect(component.calculateTextFontSize(1650)).toBeLessThan(15);
    expect(component.calculateTextFontSize(2100)).toBe(15);
  });

  it('should draw exon without cds', () => {
    const drawRectSpy = spyOn(svgDrawing, 'drawRect')
      .and.callFake((element, xStart, xEnd, y, rectThickness, title) => {
        expect(title.indexOf('CDS')).toBe(-1);
        expect(rectThickness).toBe(2);
        expect(xStart).toBe(11);
        expect(xEnd).toBe(12);
        expect(y).toBe(10);
    });

    component.drawExon(null, 11, 12, 10, 'title', false, {coding: 1, nonCoding: 2});
    expect(drawRectSpy).toHaveBeenCalled();
  });

  it('should draw exon with cds', () => {
    const drawRectWithCDSSpy = spyOn(svgDrawing, 'drawRect')
      .and.callFake((element, xStart, xEnd, y, rectThickness, title) => {
        expect(title.indexOf('CDS')).not.toBe(-1);
        expect(rectThickness).toBe(1);
        expect(xStart).toBe(11);
        expect(xEnd).toBe(12);
        expect(y).toBe(10.5);
    });

    component.drawExon(null, 11, 12, 10, 'title', true, {coding: 1, nonCoding: 2});
    expect(drawRectWithCDSSpy).toHaveBeenCalled();
  });

  it('should draw intron', () => {
    const drawLineSpy = spyOn(svgDrawing, 'drawLine')
    .and.callFake((element, xStart, xEnd, y, title) => {
      expect(xStart).toBe(11);
      expect(xEnd).toBe(12);
      expect(y).toBe(11);
      expect(title).toBe('title');
    });

    component.drawIntron(null, 11, 12, 10, 'title', {coding: 1, nonCoding: 2});
    expect(drawLineSpy).toHaveBeenCalled();
  });
});
