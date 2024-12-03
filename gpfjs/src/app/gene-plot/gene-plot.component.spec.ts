/* eslint-disable no-useless-escape */
import { SimpleChange } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Gene, Transcript } from 'app/gene-browser/gene';
import { SummaryAllelesArray, SummaryAllele } from 'app/gene-browser/summary-variants';
import { GenePlotComponent } from './gene-plot.component';

const geneMock = new Gene(
  'HGD',
  [
    new Transcript('NM_000187_1', 'chr3', '-', [
      {
        chromosome: 'chr3',
        start: 120628380,
        stop: 120682111
      }
    ], [
      {
        chromosome: 'chr3',
        start: 120628168,
        stop: 120628529
      },
      {
        chromosome: 'chr3',
        start: 120633147,
        stop: 120633328
      }
    ])
  ]
);

const summaryAllelesArray = new SummaryAllelesArray([
  new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true),
  new SummaryAllele('l2', 2, 20, 'chr', 'v2', 'CNV-', 2.00023, 2, true, false, true),
  new SummaryAllele('l3', 3, 20, 'chr', 'v3', 'missense', 3.00012, 2, true, false, true),
  new SummaryAllele('l4', 4, 20, 'chr', 'v4', 'synonymous', 4.00023, 2, true, false, true),
  new SummaryAllele('l5', 5, 20, 'chr', 'v5', 'lgds', 5.000456, 2, true, false, true),
  new SummaryAllele('l6', 6, 20, 'chr', 'v6', 'no-frame-shift', 6.000467, 2, true, false, true),
]);

describe('GenePlotComponent', () => {
  let component: GenePlotComponent;
  let fixture: ComponentFixture<GenePlotComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GenePlotComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(GenePlotComponent);
    component = fixture.componentInstance;
    Object.defineProperty(component, 'gene', { value: geneMock });
    Object.defineProperty(component, 'frequencyDomain', { value: [1, 100] });
    Object.defineProperty(component, 'allVariantsCounts', { value: [0, 0] });
    Object.defineProperty(component, 'variantsArray', { value: summaryAllelesArray });
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should draw plot', () => {
    const alleleTitleCNVPlus =
        `Effect type: ${summaryAllelesArray.summaryAlleles[0].effect}`
        + `\nPosition: ${summaryAllelesArray.summaryAlleles[0].location}`
        + `\nVariant: ${summaryAllelesArray.summaryAlleles[0].variant}`
        + `\nFrequency: ${summaryAllelesArray.summaryAlleles[0].frequency.toFixed(3).toString()}`;

    const alleleTitleCNVMinus =
      `Effect type: ${summaryAllelesArray.summaryAlleles[1].effect}`
      + `\nPosition: ${summaryAllelesArray.summaryAlleles[1].location}`
      + `\nVariant: ${summaryAllelesArray.summaryAlleles[1].variant}`
      + `\nFrequency: ${summaryAllelesArray.summaryAlleles[1].frequency.toFixed(3).toString()}`;

    const alleleTitleMissense =
      `Effect type: ${summaryAllelesArray.summaryAlleles[2].effect}`
      + `\nPosition: ${summaryAllelesArray.summaryAlleles[2].location}`
      + `\nVariant: ${summaryAllelesArray.summaryAlleles[2].variant}`
      + `\nFrequency: ${summaryAllelesArray.summaryAlleles[2].frequency.toFixed(3).toString()}`;

    const alleleTitleSynonymous =
      `Effect type: ${summaryAllelesArray.summaryAlleles[3].effect}`
      + `\nPosition: ${summaryAllelesArray.summaryAlleles[3].location}`
      + `\nVariant: ${summaryAllelesArray.summaryAlleles[3].variant}`
      + `\nFrequency: ${summaryAllelesArray.summaryAlleles[3].frequency.toFixed(3).toString()}`;

    const alleleTitleLGDs =
      `Effect type: ${summaryAllelesArray.summaryAlleles[4].effect}`
      + `\nPosition: ${summaryAllelesArray.summaryAlleles[4].location}`
      + `\nVariant: ${summaryAllelesArray.summaryAlleles[4].variant}`
      + `\nFrequency: ${summaryAllelesArray.summaryAlleles[4].frequency.toFixed(3).toString()}`;

    const alleleTitleOther =
      `Effect type: ${summaryAllelesArray.summaryAlleles[5].effect}`
      + `\nPosition: ${summaryAllelesArray.summaryAlleles[5].location}`
      + `\nVariant: ${summaryAllelesArray.summaryAlleles[5].variant}`
      + `\nFrequency: ${summaryAllelesArray.summaryAlleles[5].frequency.toFixed(3).toString()}`;

    component.ngOnChanges({ gene: new SimpleChange(null, geneMock, true) });
    component.redraw();

    const plot = fixture.nativeElement as HTMLElement;
    const triangleTitles = Array.from(plot.querySelectorAll('g polygon title'));
    const circleTitles = Array.from(plot.querySelectorAll('g circle title'));
    const rectTitles = Array.from(plot.querySelectorAll('g rect title'));
    const starTitles = Array.from(plot.querySelectorAll('svg g path title'));

    const filteredRectTitlesMissense = rectTitles.filter(item => item.textContent === alleleTitleMissense);
    const filteredTriangleTitles = triangleTitles.filter(item => item.textContent === alleleTitleMissense);
    expect(filteredRectTitlesMissense).toStrictEqual(filteredTriangleTitles);

    const filteredRectTitlesCNVPlus = rectTitles.filter(item => item.textContent === alleleTitleCNVPlus);
    expect(filteredRectTitlesCNVPlus).toHaveLength(2);

    const filteredRectTitlesCNVMinus = rectTitles.filter(item => item.textContent === alleleTitleCNVMinus);
    expect(filteredRectTitlesCNVMinus).toHaveLength(2);

    const filteredRectTitlesSynonymous = rectTitles.filter(item => item.textContent === alleleTitleSynonymous);
    const filteredCircleTitles = circleTitles.filter(item => item.textContent === alleleTitleSynonymous);
    expect(filteredRectTitlesSynonymous).toStrictEqual(filteredCircleTitles);

    const filteredRectTitlesLGDs = rectTitles.filter(item => item.textContent === alleleTitleLGDs);
    const filteredStarTitles = starTitles.filter(item => item.textContent === alleleTitleLGDs);
    expect(filteredRectTitlesLGDs).toStrictEqual(filteredStarTitles);

    const filteredRectTitlesOther = rectTitles.filter(item => item.textContent === alleleTitleOther);
    const filteredCircleTitlesOther = circleTitles.filter(item => item.textContent === alleleTitleOther);
    expect(filteredRectTitlesOther).toStrictEqual(filteredCircleTitlesOther);
  });

  it('should render no frequency text', () => {
    component.ngOnChanges({ gene: new SimpleChange(null, geneMock, true) });
    component.redraw();

    const plot = fixture.nativeElement as HTMLElement;
    const yNoFrequencySubdomain = Array.from(plot.querySelectorAll('div#svg-container'));
    expect(yNoFrequencySubdomain[0].innerHTML).toContain(
      '<g id=\"yNoFrequencyDomain\" style=\"font: sans-serif 14px 14px;\" fill=\"none\" ' +
      'font-size=\"10\" font-family=\"sans-serif\" text-anchor=\"end\">' +
      '<path class=\"domain\" stroke=\"currentColor\" d=\"M-6,310.5H0.5V288.8H-6\"></path></g>'
    );
    expect(plot.querySelectorAll('g#plot')[0].innerHTML).toContain(
      '<text style=\"text-anchor: end; font: sans-serif 14px 14px;\" x=\"-10\" y=\"303.15\">No frequency</text>'
    );
  });

  it('should render no frequency domain', () => {
    component.ngOnChanges({ gene: new SimpleChange(null, geneMock, true) });
    component.redraw();

    const plot = fixture.nativeElement as HTMLElement;
    const yNoFrequencySubdomain = Array.from(plot.querySelectorAll('g#plot'));
    expect(yNoFrequencySubdomain[0].innerHTML).toContain(
      '<rect height=\"21.69999999999999\" width=\"1835\" x=\"1\" '
        + 'y=\"288.3\" fill=\"#63b2ea\" fill-opacity=\"0.25\"></rect>'
    );
  });
});
