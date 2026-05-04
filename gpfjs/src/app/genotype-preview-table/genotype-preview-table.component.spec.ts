import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';

import { GenotypePreviewTableComponent } from './genotype-preview-table.component';
import { GpfTableComponent } from 'app/table/table.component';
import { GpfTableHeaderComponent } from 'app/table/view/header/header.component';
import { GpfTableCellComponent } from 'app/table/view/cell.component';
import { GpfTableEmptyCellComponent } from 'app/table/view/empty-cell.component';
import { GpfTableSubheaderComponent } from 'app/table/component/subheader.component';
import { GenotypeBrowser, PersonSet } from 'app/datasets/datasets';
import { GenotypePreview, GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { LegendItem } from 'app/variant-reports/variant-reports';
import { ComparePipe } from 'app/utils/compare.pipe';

describe('GenotypePreviewTableComponent', () => {
  let component: GenotypePreviewTableComponent;
  let fixture: ComponentFixture<GenotypePreviewTableComponent>;
  const comparePipe: ComparePipe = new ComparePipe();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [CUSTOM_ELEMENTS_SCHEMA],
      declarations: [
        GenotypePreviewTableComponent,
        GpfTableComponent,
        GpfTableHeaderComponent,
        GpfTableCellComponent,
        GpfTableEmptyCellComponent,
        GpfTableSubheaderComponent,
        ComparePipe
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(GenotypePreviewTableComponent);
    component = fixture.componentInstance;

    component.legend = [
      new PersonSet('id1', 'name1', 'color1'),
      new PersonSet('id2', 'name2', 'color2')
    ];
    component.columns = GenotypeBrowser.tableColumnsFromJson([
      {
        id: 'column1',
        name: 'column1',
        source: 'column1',
        columns: [
          {
            id: 'slot1',
            name: 'slot1',
            source: 'slot1',
            format: '%s'
          }
        ]
      },
      {
        id: 'column2',
        name: 'column2',
        source: 'column2',
      }
    ]);

    const columnIds = ['slot1', 'column2'];

    component.genotypePreviewVariantsArray = new GenotypePreviewVariantsArray();
    component.genotypePreviewVariantsArray.
      addPreviewVariant(['value11', 'value12'], columnIds);
    component.genotypePreviewVariantsArray.
      addPreviewVariant(['value21', 'value22'], columnIds);
    component.genotypePreviewVariantsArray.
      addPreviewVariant(['value31', 'value32'], columnIds);

    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have working comparator', () => {
    expect(comparePipe.transform('variant.location')).toBe(comparePipe.locationComparator);

    expect(comparePipe.transform('field')(
      GenotypePreview.fromJson([null], ['field']),
      GenotypePreview.fromJson([null], ['field'])
    )).toBe(0);

    expect(comparePipe.transform('field')(
      GenotypePreview.fromJson(['value1'], ['field']),
      GenotypePreview.fromJson([null], ['field'])
    )).toBe(1);

    expect(comparePipe.transform('field')(
      GenotypePreview.fromJson([null], ['field']),
      GenotypePreview.fromJson(['value1'], ['field'])
    )).toBe(-1);

    expect(comparePipe.transform('field')(
      GenotypePreview.fromJson([0], ['field']),
      GenotypePreview.fromJson([10], ['field'])
    )).toBe(-10);

    expect(comparePipe.locationComparator(
      GenotypePreview.fromJson(['X:123'], ['variant.location']),
      GenotypePreview.fromJson(['1:123'], ['variant.location'])
    )).toBe(99);

    expect(comparePipe.locationComparator(
      GenotypePreview.fromJson(['Y:125'], ['variant.location']),
      GenotypePreview.fromJson(['Y:113'], ['variant.location'])
    )).toBe(12);

    expect(comparePipe.locationComparator(
      GenotypePreview.fromJson(['Y:125'], ['variant.location']),
      GenotypePreview.fromJson(['M:113'], ['variant.location'])
    )).toBe(-1);
  });

  it('should have set legend on init', () => {
    expect(component.legend).toStrictEqual([
      new PersonSet('id1', 'name1', 'color1'),
      new PersonSet('id2', 'name2', 'color2')
    ]);
  });

  it('should have set legend item on init', () => {
    expect(component.legendItems).toStrictEqual([
      new LegendItem('id1', 'name1', 'color1'),
      new LegendItem('id2', 'name2', 'color2'),
    ]);
  });

  // it.skip('should calculate single column width in onResize()', () => {
  // const windowSpy = spyOnProperty(window, 'innerWidth');

  // windowSpy.mockReturnValue(85);
  // component.columns = new Array<any>(1);
  // component.onResize();
  // expect((component as any).singleColumnWidth).toEqual('10px');

  // windowSpy.mockReturnValue(2075);
  // component.columns = new Array<any>(10);
  // component.onResize();
  // expect((component as any).singleColumnWidth).toEqual('200px');

  // component.columns = new Array<any>(25);
  // component.onResize();
  // expect((component as any).singleColumnWidth).toEqual('80px');

  // windowSpy.mockReturnValue(1920);
  // component.columns = new Array<any>(12);
  // component.onResize();
  // expect((component as any).singleColumnWidth).toEqual('153.75px');

  // component.columns = new Array<any>(15);
  // component.onResize();
  // expect((component as any).singleColumnWidth).toEqual('123px');

  // windowSpy.mockReturnValue(1366);
  // component.columns = new Array<any>(8);
  // component.onResize();
  // expect((component as any).singleColumnWidth).toEqual('161.375px');
  // });
});
