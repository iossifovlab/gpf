import { SimpleChange } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Gene, Transcript } from 'app/gene-browser/gene';
import { SummaryAllelesArray, SummaryAllele } from 'app/gene-browser/summary-variants';
import * as d3 from 'd3';
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

const variantsArrayMock = [
  new SummaryAllele('l1', 1, 20, 'chr', 'v1', 'CNV+', 1.00003, 2, true, false, true),
  new SummaryAllele('l2', 2, 20, 'chr', 'v2', 'CNV-', 2.00023, 2, true, false, true),
  new SummaryAllele('l3', 3, 20, 'chr', 'v3', 'missense', 3.00012, 2, true, false, true),
  new SummaryAllele('l4', 4, 20, 'chr', 'v4', 'synonymous', 4.00023, 2, true, false, true),
  new SummaryAllele('l5', 5, 20, 'chr', 'v5', 'lgds', 5.000456, 2, true, false, true),
  new SummaryAllele('l6', 6, 20, 'chr', 'v6', 'no-frame-shift', 6.000467, 2, true, false, true),
];

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
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should draw plot', () => {
    const summaryAllelesArray = new SummaryAllelesArray(variantsArrayMock);
    Object.defineProperty(component, 'variantsArray', {
      value: summaryAllelesArray
    });

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

  it('should create plot with different values', () => {
    const summaryAllelesArray = new SummaryAllelesArray(variantsArrayMock);
    Object.defineProperty(component, 'variantsArray', {
      value: summaryAllelesArray
    });
    component.ngOnChanges({ gene: new SimpleChange(null, geneMock, true) });
    component.redraw();
    const plot = fixture.nativeElement as HTMLElement;
    [
      Array.from(plot.querySelectorAll('g polygon')),
      Array.from(plot.querySelectorAll('g rect')),
      Array.from(plot.querySelectorAll('svg g path'))
    ].forEach((variantType, i) => {
      expect(variantType).toHaveLength([1, 25, 5][i]);
    });
    Object.defineProperty(component, 'variantsArray', {
      value: new SummaryAllelesArray([])
    });
    component.ngOnChanges({ gene: new SimpleChange(null, geneMock, true) });
    component.redraw();
    [
      Array.from(plot.querySelectorAll('g polygon')),
      Array.from(plot.querySelectorAll('g rect')),
      Array.from(plot.querySelectorAll('svg g path'))
    ].forEach((variantType, i) => {
      expect(variantType).toHaveLength([0, 17, 4][i]);
    });
  });

  it('should check viewbox and dimensions', () => {
    const summaryAllelesArray = new SummaryAllelesArray(variantsArrayMock);
    Object.defineProperty(component, 'variantsArray', {
      value: summaryAllelesArray
    });
    component.ngOnChanges({ gene: new SimpleChange(null, geneMock, true) });
    component.redraw();
    expect(d3.selectAll('svg g rect').attr('height')).toBe('22');
    expect(d3.selectAll('svg g rect').attr('width')).toBe('1835');
    expect(d3.selectAll('#svg-container svg').attr('viewBox')).toBe('0 0 2000 517');
  });

  it('should call draw transcript on single chromosome', () => {
    const spyOnDrawTranscript = jest.spyOn(component, 'drawTranscript');
    const summaryAllelesArray = new SummaryAllelesArray(variantsArrayMock);
    Object.defineProperty(component, 'variantsArray', {
      value: summaryAllelesArray
    });
    component.ngOnChanges({ gene: new SimpleChange(null, geneMock, true) });
    component.redraw();
    expect(spyOnDrawTranscript).toHaveBeenCalledTimes(4);
    expect(spyOnDrawTranscript.mock.calls[0][1]).toStrictEqual(new Transcript('collapsed', 'chr3', '-', [
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
    ]));
  });

  it('should call draw transcript on multiple chromosomes', () => {
    const genes = new Gene(
      'HGD',
      [
        new Transcript(
          'id1',
          'chrom1',
          '1',
          [{ chromosome: 'chrom1', start: 1, stop: 5 }],
          [{ chromosome: 'chrom1', start: 7, stop: 11 },
            { chromosome: 'chrom2', start: 20, stop: 25 }]
        ),
        new Transcript(
          'id2',
          'chrom2',
          '1',
          [{ chromosome: 'chrom3', start: 3, stop: 4 }],
          [{ chromosome: 'chrom3', start: 13, stop: 16 },
            { chromosome: 'chrom7', start: 18, stop: 22 }]
        ),
        new Transcript(
          'id3',
          'chrom3',
          '1',
          [{ chromosome: 'chrom1', start: 7, stop: 15 }],
          [{ chromosome: 'chrom2', start: 3, stop: 16 },
            { chromosome: 'chrom3', start: 18, stop: 35 }]
        )
      ]
    );

    const spyOnDrawTranscript = jest.spyOn(component, 'drawTranscript');
    const summaryAllelesArray = new SummaryAllelesArray(variantsArrayMock);
    Object.defineProperty(component, 'variantsArray', {
      value: summaryAllelesArray
    });
    Object.defineProperty(component, 'gene', { value: genes });
    component.ngOnChanges({ gene: new SimpleChange(null, genes, true) });
    component.redraw();
    expect(spyOnDrawTranscript).toHaveBeenCalledTimes(12);
    [
      [
        new Transcript(
          'collapsed',
          'chrom1',
          '1',
          [
            { chromosome: 'chrom1', start: 1, stop: 5 }
          ],
          [
            { chromosome: 'chrom1', start: 7, stop: 11 },
            { chromosome: 'chrom2', start: 20, stop: 25 }
          ]
        ), 362, false],
      [
        new Transcript('collapsed', 'chrom2', '1',
          [
            {
              chromosome: 'chrom3', start: 3, stop: 4
            }
          ],
          [
            { chromosome: 'chrom3', start: 13, stop: 16 },
            { chromosome: 'chrom7', start: 18, stop: 22 }
          ]
        ), 422, true]
    ].forEach((args, i) => {
      args.forEach((data, y) => {
        expect(spyOnDrawTranscript.mock.calls[i][y + 1]).toStrictEqual(data);
      });
    });
  });
});
