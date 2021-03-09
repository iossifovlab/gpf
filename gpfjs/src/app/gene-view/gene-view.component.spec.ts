import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { UsersService } from 'app/users/users.service';
import * as draw from 'app/utils/svg-drawing';
import * as d3 from 'd3';
// import * as d3Selection from 'd3-selection';
const d3Selection = require('d3-selection');
// tslint:disable-next-line:import-blacklist
import { Subject, Observable } from 'rxjs';
import { Gene, GeneViewSummaryAllele, GeneViewSummaryAllelesArray, Transcript } from './gene';
import { GeneViewModel, GeneViewTranscript } from './gene-view';

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

interface MutableEvent { selection: any; }
interface MutableD3 { event: MutableEvent; }

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
      'regions': ['regions'],
      'summaryVariantIds': [],
      'selectedVariantTypes': [ 'sub', 'ins', 'del', 'cnv+', 'cnv-' ]
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
    const drawTypes: any = ['star', 'triangle', 'circle', 'dot'];
    const iconTitles = ['LGDs', 'Missense', 'Synonymous', 'Other'];

    const drawSpies = [];
    drawTypes.forEach((drawType, index) => {
      drawSpies[index] = spyOn(draw, drawType).and.callFake((element, x, y, color, title) => {
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
    const drawTypes: any = ['star', 'triangle', 'circle', 'dot'];
    const iconTitles = ['Denovo LGDs', 'Denovo Missense', 'Denovo Synonymous', 'Denovo Other'];

    const drawSurroundingSquareSpy = spyOn(draw, 'surroundingRectangle');
    const drawSpies = [];
    drawTypes.forEach((drawType, index) => {
      drawSpies[index] = spyOn(draw, drawType).and.callFake((element, x, y, color, title) => {
        expect(element).toEqual(component.svgElement);
        expect(title).toEqual(iconTitles[index]);
      });
    });
    let cnvPlusDrawn = false;
    let cnvMinusDrawn = false;
    const drawCnvSpy = spyOn(draw, 'rect').and.callFake((element, xStart, xEnd, y, height, color, opacity, title) => {
      expect(element).toEqual(component.svgElement);
      if (title === 'Denovo CNV+') {
        cnvPlusDrawn = true;
      } else if (title === 'Denovo CNV-') {
        cnvMinusDrawn = true;
      }
    });

    component.drawDenovoIcons();

    for (const drawSpy of drawSpies) {
      expect(drawSpy).toHaveBeenCalled();
    }
    expect(cnvPlusDrawn).toBeTrue();
    expect(cnvMinusDrawn).toBeTrue();
    expect(drawCnvSpy).toHaveBeenCalledTimes(2);
    expect(drawSurroundingSquareSpy).toHaveBeenCalledTimes(6);
  });

  it('should draw effect types icons with correct shapes and titles', () => {
    const drawTypes: any = ['star', 'triangle', 'circle', 'dot'];
    const iconTitles = ['#LGDs', '#Missense', '#Synonymous', '#Other'];

    const drawSpies = [];
    drawTypes.forEach((drawType, index) => {
      drawSpies[index] = spyOn(draw, drawType).and.callFake((element, x, y, color, title) => {
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
    const setDenovoPlotHeightSpy = spyOn(component, 'setDenovoPlotHeight');
    const redrawSpy = spyOn(component, 'redraw');
    const updateFamilyVariantsTableSpy = spyOn(component, 'updateFamilyVariantsTable');

    component.redrawAndUpdateTable();
    expect(setDenovoPlotHeightSpy).toHaveBeenCalled();
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

  it('should check hide transcripts', () => {
    component.svgElement = d3.select('#svg-container');
    component.transcriptsElement = component.svgElement.append('g');
    let checked;
    const addAttributeSpy = spyOn(component.transcriptsElement, 'attr').and.callFake((attr, value) => {
      expect(attr).toBe('display');
      if (checked) {
        expect(value).toBe('none');
      } else {
        expect(value).toBe('block');
      }
    });

    checked = true;
    component.checkHideTranscripts(checked);
    expect(addAttributeSpy).toHaveBeenCalled();

    checked = false;
    component.checkHideTranscripts(checked);
    expect(addAttributeSpy).toHaveBeenCalledTimes(2);
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

  it('should get different colors for Affected Statuses', () => {
    const affectedColor = component.getAffectedStatusColor('Affected only');
    const unaffectedColor = component.getAffectedStatusColor('Unaffected only');
    const otherColor = component.getAffectedStatusColor('Other status');

    expect(affectedColor).not.toEqual(unaffectedColor);
    expect(affectedColor).not.toEqual(otherColor);
    expect(unaffectedColor).not.toEqual(otherColor);
  });

  it('should get a variant\'s Affected Status', () => {
    let testVariant = GeneViewSummaryAllele.fromRow({ seen_in_affected: true, seen_in_unaffected: true });
    expect(component.getVariantAffectedStatus(testVariant)).toBe('Affected and unaffected');

    testVariant = GeneViewSummaryAllele.fromRow({ seen_in_affected: true, seen_in_unaffected: false });
    expect(component.getVariantAffectedStatus(testVariant)).toBe('Affected only');

    testVariant = GeneViewSummaryAllele.fromRow({ seen_in_affected: false, seen_in_unaffected: true });
    expect(component.getVariantAffectedStatus(testVariant)).toBe('Unaffected only');
  });

  it('should see if Affected Status is selected', () => {
    spyOn(component, 'redrawAndUpdateTable');
    component.checkAffectedStatus('Affected only', false);
    expect(component.isAffectedStatusSelected('Affected only')).toBeFalse();
    component.checkAffectedStatus('Affected only', true);
    expect(component.isAffectedStatusSelected('Affected only')).toBeTrue();
  });

  it('should filter summary variants array', () => {
    component.selectedFrequencies = [10, 20];
    component.selectedEffectTypes = ['missense', 'synonymous'];
    component.selectedAffectedStatus = ['Affected only'];
    component.showDenovo = false;

    const testVariant1 = GeneViewSummaryAllele.fromRow({
      effect: 'missense', is_denovo: false, seen_in_affected: true, seen_in_unaffected: false, frequency: 15, position: 15, variant: 'sub'
    });

    const testVariant2 = GeneViewSummaryAllele.fromRow({
      effect: 'lgds', is_denovo: false, seen_in_affected: true, seen_in_unaffected: false, frequency: 15, position: 15, variant: 'del'
    });

    const testVariant3 = GeneViewSummaryAllele.fromRow({
      effect: 'missense', is_denovo: true, seen_in_affected: true, seen_in_unaffected: false, frequency: 15, position: 15, variant: 'ins'
    });

    const testVariant4 = GeneViewSummaryAllele.fromRow({
      effect: 'missense', is_denovo: false, seen_in_affected: false, seen_in_unaffected: true, frequency: 15, position: 15, variant: 'cnv+'
    });

    const testVariant5 = GeneViewSummaryAllele.fromRow({
      effect: 'missense', is_denovo: false, seen_in_affected: false, seen_in_unaffected: true, frequency: 9, position: 15, variant: 'cnv-'
    });

    const testVariant6 = GeneViewSummaryAllele.fromRow({
      effect: 'missense', is_denovo: false, seen_in_affected: false, seen_in_unaffected: true, frequency: 15, position: 9, variant: 'cnv+'
    });

    const variantsArray = new GeneViewSummaryAllelesArray();
    variantsArray.addSummaryAllele(testVariant1);
    variantsArray.addSummaryAllele(testVariant2);
    variantsArray.addSummaryAllele(testVariant3);
    variantsArray.addSummaryAllele(testVariant4);
    variantsArray.addSummaryAllele(testVariant5);
    variantsArray.addSummaryAllele(testVariant6);

    const filteredVariantsArray = component.filterSummaryVariantsArray(variantsArray, 10, 20);
    expect(filteredVariantsArray.summaryAlleles.indexOf(testVariant1)).not.toBe(-1);
    expect(filteredVariantsArray.summaryAlleles.indexOf(testVariant2)).toBe(-1);
    expect(filteredVariantsArray.summaryAlleles.indexOf(testVariant3)).toBe(-1);
    expect(filteredVariantsArray.summaryAlleles.indexOf(testVariant4)).toBe(-1);
    expect(filteredVariantsArray.summaryAlleles.indexOf(testVariant5)).toBe(-1);
    expect(filteredVariantsArray.summaryAlleles.indexOf(testVariant6)).toBe(-1);
  });

  it('should get pedigree affected status', () => {
    let mockPedigreeData = [ {'label': 0, 'color': ''}, {'label': 1, 'color': '#ffffff'} ];
    expect(component.getPedigreeAffectedStatus(mockPedigreeData)).toBe('Unaffected only');

    mockPedigreeData = [ {'label': 0, 'color': ''}, {'label': 1, 'color': 'other'} ];
    expect(component.getPedigreeAffectedStatus(mockPedigreeData)).toBe('Affected only');

    mockPedigreeData = [ {'label': 1, 'color': '#ffffff'}, {'label': 1, 'color': 'other'} ];
    expect(component.getPedigreeAffectedStatus(mockPedigreeData)).toBe('Affected and unaffected');
  });

  it('should draw correct shapes for variants when drawing the plot', () => {
    component.selectedFrequencies = [0, 100];
    component.selectedAffectedStatus = ['Affected only'];
    component.showDenovo = false;
    component.x = d3.scaleLinear().domain([1, 100]).range([1, 100]).clamp(true);
    component.y = d3.scaleLog()
      .domain([component.frequencyDomainMin, component.frequencyDomainMax])
      .range([component.subdomainAxisY, 0]);
    component.y_subdomain = d3.scaleLinear()
      .domain([0, 0])
      .range([component.zeroAxisY, component.subdomainAxisY]);
    component.y_zero = d3.scalePoint()
      .domain(['0'])
      .range([component.svgHeightFreq, component.zeroAxisY]);
    component.svgElement = d3.select('#svg-container');
    component.showDenovo = true;
    const drawTypes: any = ['star', 'triangle', 'circle', 'dot'];
    const effectTypes = ['lgds', 'missense', 'synonymous', 'other'];

    const drawSpies = [];
    drawTypes.forEach((drawType, index) => {
      drawSpies[index] = spyOn(draw, drawType).and.callFake((element, x, y, color, title) => {
        expect(title.indexOf(effectTypes[index])).not.toBe(-1);
      });
    });
    const drawRectSpy = spyOn(draw, 'rect').and.callFake((element, x, xEnd, y, height, color, opacity, title) => {
      expect(title.indexOf('CNV+')).not.toBe(-1);
    });

    const drawSurroundingSquareSpy = spyOn(draw, 'surroundingRectangle');

    const testVariant1 = GeneViewSummaryAllele.fromRow({
      effect: 'lgds', is_denovo: true, seen_in_affected: true, seen_in_unaffected: false, frequency: 15, position: 15, variant: 'sub'
    });

    const testVariant2 = GeneViewSummaryAllele.fromRow({
      effect: 'missense', is_denovo: false, seen_in_affected: true, seen_in_unaffected: false, frequency: 15, position: 15, variant: 'ins'
    });

    const testVariant3 = GeneViewSummaryAllele.fromRow({
      effect: 'synonymous', is_denovo: false, seen_in_affected: true, seen_in_unaffected: false, frequency: 15, position: 15, variant: 'del'
    });

    const testVariant4 = GeneViewSummaryAllele.fromRow({
      effect: 'other', is_denovo: false, seen_in_affected: true, seen_in_unaffected: false, frequency: 15, position: 15, variant: 'del'
    });

    const testVariant5 = GeneViewSummaryAllele.fromRow({
      effect: 'CNV+', is_denovo: false, seen_in_affected: true, seen_in_unaffected: false, frequency: 15, position: 15, endPosition: 25, variant: 'cnv+'
    });

    component.summaryVariantsArray = new GeneViewSummaryAllelesArray();
    component.summaryVariantsArray.addSummaryAllele(testVariant1);
    component.summaryVariantsArray.addSummaryAllele(testVariant2);
    component.summaryVariantsArray.addSummaryAllele(testVariant3);
    component.summaryVariantsArray.addSummaryAllele(testVariant4);
    component.summaryVariantsArray.addSummaryAllele(testVariant5);

    component.drawPlot();

    expect(drawSurroundingSquareSpy).toHaveBeenCalled();
    expect(drawSurroundingSquareSpy).toHaveBeenCalledTimes(1);
    // FIXME:
    // for (const drawSpy of drawSpies) {
    //   expect(drawSpy).toHaveBeenCalled();
    //   expect(drawSpy).toHaveBeenCalledTimes(1);
    // }
    expect(drawRectSpy).toHaveBeenCalled();
    expect(drawRectSpy).toHaveBeenCalledTimes(1);
  });

  it('should draw denovo variants with spacings when drawing the plot', () => {
    component.selectedFrequencies = [0, 100];
    component.selectedAffectedStatus = ['Affected only'];
    component.showDenovo = true;
    component.x = d3.scaleLinear().domain([1, 100]).range([1, 100]).clamp(true);
    component.y = d3.scaleLog()
      .domain([component.frequencyDomainMin, component.frequencyDomainMax])
      .range([component.subdomainAxisY, 100]);
    component.y_subdomain = d3.scaleLinear()
      .domain([0, 100])
      .range([component.zeroAxisY, component.subdomainAxisY]);
    component.y_zero = d3.scalePoint()
      .domain(['0'])
      .range([component.svgHeightFreq, component.zeroAxisY]);
    component.svgElement = d3.select('#svg-container');
    component.showDenovo = true;
    const getVariantYSpy = spyOn(component, 'getVariantY').and.callFake(y => {return y;});

    const spacings: Number[] = [];
    const drawSpy = spyOn(draw, 'star').and.callFake((element, x, y, color, title) => {
      spacings.push(y);
    });

    component.summaryVariantsArray = new GeneViewSummaryAllelesArray();
    component.summaryVariantsArray.addSummaryAlleleRow({
      effect: 'lgds', is_denovo: true, seen_in_affected: true, seen_in_unaffected: false, frequency: null, position: 1, variant: 'sub', location: '1'
    })
    component.summaryVariantsArray.addSummaryAlleleRow({
      effect: 'lgds', is_denovo: true, seen_in_affected: true, seen_in_unaffected: false, frequency: null, position: 1, variant: 'sub', location: '2'
    })
    component.summaryVariantsArray.addSummaryAlleleRow({
      effect: 'lgds', is_denovo: true, seen_in_affected: true, seen_in_unaffected: false, frequency: null, position: 1, variant: 'sub', location: '3'
    })
    component.summaryVariantsArray.addSummaryAlleleRow({
      effect: 'lgds', is_denovo: true, seen_in_affected: true, seen_in_unaffected: false, frequency: null, position: 1, variant: 'sub', location: '4'
    })
    component.summaryVariantsArray.addSummaryAlleleRow({
      effect: 'lgds', is_denovo: true, seen_in_affected: true, seen_in_unaffected: false, frequency: null, position: 1, variant: 'sub', location: '5'
    })

    component.denovoAllelesSpacings = {
      '1:sub': 10,
      '2:sub': 20,
      '3:sub': 30,
      '4:sub': 40,
      '5:sub': 50,
    }

    component.drawPlot();
    expect(spacings).toEqual([18, 28, 38, 48, 58]);
  });

  it('should calculate correct spacings for denovo variants', () => {
    component.x = d3.scaleLinear().domain([1, 100]).range([1, 100]).clamp(true);
    let result;
    const spacingValue = 22;

    // denovo + non denovo
    let variantsArray = new GeneViewSummaryAllelesArray();
    variantsArray.addSummaryAlleleRow({
      is_denovo: false, frequency: 15, position: 15, end_position: 15, variant: 'nonDenovoVariant1'
    });
    variantsArray.addSummaryAlleleRow({
      is_denovo: true, frequency: null, position: 15, end_position: 15, variant: 'denovoVariant1'
    });

    result = component.calculateDenovoAllelesSpacings(variantsArray);
    expect(Object.keys(result).indexOf('nonDenovoVariant1')).toBe(-1);
    expect(result).toEqual({'undefined:denovoVariant1': 0});

    // 3 denovos and 1 CNV denovo intersecting
    variantsArray = new GeneViewSummaryAllelesArray();
    variantsArray.addSummaryAlleleRow({
      is_denovo: true, frequency: null, position: 15, variant: 'denovoVariant1'
    });
    variantsArray.addSummaryAlleleRow({
      is_denovo: true, frequency: null, position: 15, variant: 'denovoVariant2'
    });
    variantsArray.addSummaryAlleleRow({
      is_denovo: true, frequency: null, position: 21, variant: 'denovoVariant3'
    });
    variantsArray.addSummaryAlleleRow({
      is_denovo: true, frequency: null, position: 1, end_position: 30, effect: 'CNV+', variant: 'denovoCnvVariant1'
    });

    result = component.calculateDenovoAllelesSpacings(variantsArray);
    expect(Object.keys(result).length).toBe(4);
    expect(Object.values(result).sort()).toEqual([0, spacingValue, 2 * spacingValue, 3 * spacingValue]);

    // 2 denovos not intersecting
    variantsArray = new GeneViewSummaryAllelesArray();

    variantsArray.addSummaryAlleleRow({
      is_denovo: true, frequency: null, position: 10, variant: 'denovoVariant1'
    });
    variantsArray.addSummaryAlleleRow({
      is_denovo: true, frequency: null, position: 30, variant: 'denovoVariant2'
    });

    result = component.calculateDenovoAllelesSpacings(variantsArray);
    expect(Object.keys(result).length).toBe(2);
    expect(Object.values(result).sort()).toEqual([0, 0]);

    // 2 CNV denovos intersecting and 1 not intersecting
    variantsArray = new GeneViewSummaryAllelesArray();

    variantsArray.addSummaryAlleleRow({
      is_denovo: true, frequency: null, position: 10, end_position: 20, effect: 'CNV+', variant: 'denovoCnvVariant1'
    });
    variantsArray.addSummaryAlleleRow({
      is_denovo: true, frequency: null, position: 15, end_position: 25, effect: 'CNV+', variant: 'denovoCnvVariant2'
    });
    variantsArray.addSummaryAlleleRow({
      is_denovo: true, frequency: null, position: 35, end_position: 45, effect: 'CNV+', variant: 'denovoCnvVariant3'
    });

    result = component.calculateDenovoAllelesSpacings(variantsArray);
    expect(Object.keys(result).length).toBe(3);
    expect(Object.values(result).sort()).toEqual([0, 0, 22]);
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

  it('should draw gene transcripts', () => {
    component.x = d3.scaleLinear().domain([1, 10]).range([1, 10]).clamp(true);
    component.svgElement = d3.select('#svg-container');
    component.summedTranscriptElement = component.svgElement
      .append('g');
    component.transcriptsElement = component.svgElement
      .append('g');

    const drawTranscriptSpy = spyOn(component, 'drawTranscript')
      .withArgs(component.summedTranscriptElement, component.svgHeightFreqRaw + 30, component.geneViewModel.collapsedGeneViewTranscript)
      .and.stub()
      .withArgs(component.transcriptsElement, component.svgHeightFreqRaw + 80, component.geneViewModel.geneViewTranscripts[0])
      .and.stub()
      .withArgs(component.transcriptsElement, component.svgHeightFreqRaw + 105, component.geneViewModel.geneViewTranscripts[1])
      .and.stub();

    component.drawGene();
    expect(drawTranscriptSpy).toHaveBeenCalled();
  });

  it('should update brush with new d3 selection', () => {
    const selectionMock = [[1, 11], [2, 12]];
    component.x = d3.scaleLinear().domain([0, 0]).range([0, 0]).clamp(true);
    const setDefaultScaleSpy = spyOn(component, 'setDefaultScale');
    const redrawAndUpdateTableSpy = spyOn(component, 'redrawAndUpdateTable');

    component.doubleClickTimer = 0;
    component.updateBrush(null);
    expect(component.doubleClickTimer).not.toEqual(0);
    expect(setDefaultScaleSpy).not.toHaveBeenCalled();
    expect(redrawAndUpdateTableSpy).not.toHaveBeenCalled();

    component.doubleClickTimer = 1;
    component.updateBrush(null);
    expect(component.doubleClickTimer).toBe(1);
    expect(setDefaultScaleSpy).toHaveBeenCalled();
    expect(redrawAndUpdateTableSpy).toHaveBeenCalled();

    component.x = d3.scaleLinear().domain([1, 2]).range([1, 10]).clamp(true);

    const addStateToHistorySpy = spyOn(component.zoomHistory, 'addStateToHistory').and.callFake((scaleState) => {
      expect(scaleState.xDomain).toEqual(component.x.domain());
      expect(scaleState.yMin).toEqual(11);
      expect(scaleState.yMax).toEqual(12);
    });
    spyOn(component, 'convertBrushPointToFrequency').and.callFake((point) => point);
    component.svgElement = d3.select('#svg-container');
    component.brush = {move: 'brushMove'};
    const svgElementSelectSpy = spyOn(component.svgElement, 'select').withArgs('.brush').and.returnValue({call(brush, somth) {}});

    component.updateBrush(selectionMock);
    expect(component.selectedFrequencies).toEqual([11, 12]);
    expect(addStateToHistorySpy).toHaveBeenCalled();
    expect(svgElementSelectSpy).toHaveBeenCalled();
    expect(redrawAndUpdateTableSpy).toHaveBeenCalledTimes(2);

    component.x = d3.scaleLinear().domain([1, 20]).range([1, 10]).clamp(true);
    component.updateBrush(selectionMock);
    expect(component.x.domain()).not.toEqual([1, 20]);
    expect(component.x.range()).not.toEqual([1, 10]);
    expect(redrawAndUpdateTableSpy).toHaveBeenCalledTimes(3);
  });

  it('should update X domain', () => {
    component.x = undefined;
    component.updateXDomain(1, 20);
    expect(component.x.domain()).toEqual(component.geneViewModel.buildDomain(1, 20));
    expect(component.x.range()).toEqual(component.recalculateXRange(1, 20));
    expect(component.x.clamp()).toEqual(true);

    component.updateXDomain(2, 12);
    expect(component.x.domain()).toEqual(component.geneViewModel.buildDomain(1, 13));
    expect(component.x.range()).toEqual(component.recalculateXRange(1, 13));
    expect(component.x.clamp()).toEqual(true);
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

  it('should handle window resize events', () => {
    component.x = d3.scaleLinear().domain([1, 10]).range([1, 10]).clamp(true);
    const setTimeoutSpy = spyOn(window, 'setTimeout');
    const setSvgScaleSpy = spyOn(component, 'setSvgScale');
    const redrawSpy = spyOn(component, 'redraw');

    component.windowResizeTimer = 0;
    component.handleWindowResizeEvent({currentTarget: {innerWidth: 10}});
    expect(setTimeoutSpy).toHaveBeenCalled();
    expect(setSvgScaleSpy).not.toHaveBeenCalled();
    expect(redrawSpy).not.toHaveBeenCalled();

    component.windowResizeTimer = 10;
    component.gene = undefined;
    component.handleWindowResizeEvent({currentTarget: {innerWidth: 10}});
    expect(setSvgScaleSpy).not.toHaveBeenCalled();
    expect(redrawSpy).not.toHaveBeenCalled();

    component.gene = testGene;
    component.handleWindowResizeEvent({currentTarget: {innerWidth: 10}});
    expect(setSvgScaleSpy).toHaveBeenCalled();
    expect(redrawSpy).toHaveBeenCalled();
  });

  it('should get selected chromosomes', () => {
    component.x = d3.scaleLinear().domain([1, 10]).range([1, 10]).clamp(true);
    let testTranscript = new GeneViewTranscript(Transcript.fromJson({
      'chrom': 'testChrom',
      'cds': [1, 100],
      'exons': [{'start': 1, 'stop': 11}, {'start': 12, 'stop': 23}]
    }));
    expect(component.getSelectedChromosomes(testTranscript)).toEqual({testChrom: [1, 23]});

    testTranscript = new GeneViewTranscript(Transcript.fromJson({
      'chrom': 'testChrom',
      'cds': [50, 100],
      'exons': [{'start': 0, 'stop': 0}, {'start': 0, 'stop': 0}]
    }));
    expect(component.getSelectedChromosomes(testTranscript)).toEqual({});
  });

  it('should draw chromosome labels ', () => {
    component.x = d3.scaleLinear().domain([0, 1]).range([0, 10]).clamp(true);
    const testTranscript = new GeneViewTranscript(Transcript.fromJson({
      'transcript_id': 'testTranscriptId',
      'strand': 'testStrand',
      'chrom': 'testChrom',
      'cds': [1, 100],
      'exons': [{'start': 1, 'stop': 11}, {'start': 12, 'stop': 23}]
    }));
    const drawHoverTextSpy = spyOn(draw, 'hoverText').and.callFake((element, x, y, title) => {
      expect(title.indexOf('testChrom')).not.toBe(-1);
    });

    component.drawChromosomeLabels(component.svgElement, 0, testTranscript);
    expect(drawHoverTextSpy).toHaveBeenCalled();
  });

  it('should calculate X axis ticks', () => {
    component.x = d3.scaleLinear().domain([0, 50]).range([0, 10]).clamp(true);
    expect(component.calculateXAxisTicks()).toEqual([ 0, 5, 10, 15, 20, 25, 30, 35, 40, 45 ]);

    component.x = d3.scaleLinear().domain([0, 100]).range([0, 10]).clamp(true);
    expect(component.calculateXAxisTicks()).toEqual([ 0, 10, 20, 30, 40, 50, 60, 70, 80, 90 ]);
  });

  it('should calculate Y axis ticks', () => {
    component.frequencyDomainMin = 1;
    component.frequencyDomainMax = 100;
    expect(component.calculateYAxisTicks()).toEqual([ 1, 10, 100 ]);
  });

  it('should calculate text font size', () => {
    expect(component.calculateTextFontSize(1200)).toBe(12);
    expect(component.calculateTextFontSize(1650)).toBeGreaterThan(12);
    expect(component.calculateTextFontSize(1650)).toBeLessThan(15);
    expect(component.calculateTextFontSize(2100)).toBe(15);
  });

  it('should draw exon without cds', () => {
    const drawRectSpy = spyOn(draw, 'rect')
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

  it('should draw transcript exons and introns correctly', () => {
    component.svgElement = d3.select('#svg-container')
        .append('svg')
        .append('g')
        .attr('transform', `translate(${component.options.margin.left}, ${component.options.margin.top})`);
    component.x = d3.scaleLinear().domain([0, 30]).range([0, 30]).clamp(true);
    const testTranscript = new GeneViewTranscript(Transcript.fromJson({
      'transcript_id': 'testTranscriptId',
      'strand': 'testStrand',
      'chrom': 'testChrom',
      'cds': [0, 100],
      'exons': [{'start': 1, 'stop': 10}, {'start': 15, 'stop': 25}]
    }));

    let firstExonDrawn = false;
    const drawExonSpy = spyOn(component, 'drawExon').and.callFake((element, xStart, xEnd, y, title, cds, brushSize) => {
      if (!firstExonDrawn) {
        expect(xStart).toBe(1);
        expect(xEnd).toBe(10);
        firstExonDrawn = true;
      } else {
        expect(xStart).toBe(15);
        expect(xEnd).toBe(25);
      }
    });
    const drawIntronSpy = spyOn(component, 'drawIntron').and.callFake((element, xStart, xEnd, y, title, brushSize) => {
      expect(xStart).toBe(10);
      expect(xEnd).toBe(15);
    });

    component.drawTranscript(component.svgElement, 0, testTranscript);
    expect(drawExonSpy).toHaveBeenCalled();
    expect(drawIntronSpy).toHaveBeenCalled();
  });

  it('should draw exon with cds', () => {
    const drawRectWithCDSSpy = spyOn(draw, 'rect')
      .and.callFake((element, xStart, xEnd, y, rectThickness, color, opacity, title) => {
        expect(title.indexOf('CDS')).not.toBe(-1);
        expect(rectThickness).toBe(1);
        expect(color).toBe('black');
        expect(opacity).toBe(1);
        expect(xStart).toBe(11);
        expect(xEnd).toBe(12);
        expect(y).toBe(10.5);
    });

    component.drawExon(null, 11, 12, 10, 'title', true, {coding: 1, nonCoding: 2});
    expect(drawRectWithCDSSpy).toHaveBeenCalled();
  });

  it('should draw intron', () => {
    const drawLineSpy = spyOn(draw, 'line')
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
