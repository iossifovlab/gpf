import { SimpleChange, SimpleChanges } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Gene, Transcript } from 'app/gene-browser/gene';
import { SummaryAllelesArray } from 'app/gene-browser/summary-variants';
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

const variantsArrayMock = {alleles: [{
  location: 'l1',
  position: 1,
  end_position: 20,
  chrom: 'chr',
  variant: 'v1',
  effect: 'CNV+',
  frequency: 1.000,
  family_variants_count: 2,
  is_denovo: true,
  seen_in_affected: false,
  seen_in_unaffected: true
},
{
  location: 'l2',
  position: 2,
  end_position: 20,
  chrom: 'chr',
  variant: 'v2',
  effect: 'CNV-',
  frequency: 2.000,
  family_variants_count: 2,
  is_denovo: true,
  seen_in_affected: false,
  seen_in_unaffected: true
},
{
  location: 'l3',
  position: 3,
  end_position: 20,
  chrom: 'chr',
  variant: 'v3',
  effect: 'missense',
  frequency: 3.000,
  family_variants_count: 2,
  is_denovo: true,
  seen_in_affected: false,
  seen_in_unaffected: true
},
{
  location: 'l4',
  position: 4,
  end_position: 20,
  chrom: 'chr',
  variant: 'v4',
  effect: 'synonymous',
  frequency: 4.000,
  family_variants_count: 2,
  is_denovo: true,
  seen_in_affected: false,
  seen_in_unaffected: true
},
{
  location: 'l5',
  position: 5,
  end_position: 20,
  chrom: 'chr',
  variant: 'v5',
  effect: 'lgds',
  frequency: 5.000,
  family_variants_count: 2,
  is_denovo: true,
  seen_in_affected: false,
  seen_in_unaffected: true
},
{
  location: 'l6',
  position: 6,
  end_position: 20,
  chrom: 'chr',
  variant: 'v6',
  effect: 'no-frame-shift',
  frequency: 6.000,
  family_variants_count: 2,
  is_denovo: true,
  seen_in_affected: false,
  seen_in_unaffected: true
}
]};

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
    (component.allVariantsCounts as [number, number]) = [0, 0];

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should draw plot', () => {
    const summaryAllelesArray = new SummaryAllelesArray();
    summaryAllelesArray.addSummaryRow(variantsArrayMock);
    Object.defineProperty(component, 'variantsArray', {
      value: summaryAllelesArray
    });

    const alleleTitleCNVPlus =
        `Effect type: ${variantsArrayMock.alleles[0].effect}`
        + `\nPosition: ${variantsArrayMock.alleles[0].location}`
        + `\nVariant: ${variantsArrayMock.alleles[0].variant}`
        + `\nFrequency: ${variantsArrayMock.alleles[0].frequency.toFixed(3).toString()}`;

    const alleleTitleCNVMinus =
      `Effect type: ${variantsArrayMock.alleles[1].effect}`
      + `\nPosition: ${variantsArrayMock.alleles[1].location}`
      + `\nVariant: ${variantsArrayMock.alleles[1].variant}`
      + `\nFrequency: ${variantsArrayMock.alleles[1].frequency.toFixed(3).toString()}`;

    const alleleTitleMissense =
      `Effect type: ${variantsArrayMock.alleles[2].effect}`
      + `\nPosition: ${variantsArrayMock.alleles[2].location}`
      + `\nVariant: ${variantsArrayMock.alleles[2].variant}`
      + `\nFrequency: ${variantsArrayMock.alleles[2].frequency.toFixed(3).toString()}`;

    const alleleTitleSynonymous =
      `Effect type: ${variantsArrayMock.alleles[3].effect}`
      + `\nPosition: ${variantsArrayMock.alleles[3].location}`
      + `\nVariant: ${variantsArrayMock.alleles[3].variant}`
      + `\nFrequency: ${variantsArrayMock.alleles[3].frequency.toFixed(3).toString()}`;

    const alleleTitleLGDs =
      `Effect type: ${variantsArrayMock.alleles[4].effect}`
      + `\nPosition: ${variantsArrayMock.alleles[4].location}`
      + `\nVariant: ${variantsArrayMock.alleles[4].variant}`
      + `\nFrequency: ${variantsArrayMock.alleles[4].frequency.toFixed(3).toString()}`;

    const alleleTitleOther =
      `Effect type: ${variantsArrayMock.alleles[5].effect}`
      + `\nPosition: ${variantsArrayMock.alleles[5].location}`
      + `\nVariant: ${variantsArrayMock.alleles[5].variant}`
      + `\nFrequency: ${variantsArrayMock.alleles[5].frequency.toFixed(3).toString()}`;

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
});
