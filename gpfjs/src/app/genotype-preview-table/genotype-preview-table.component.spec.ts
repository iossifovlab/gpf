import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';

import { GenotypePreviewTableComponent } from './genotype-preview-table.component';
import { GpfTableComponent } from 'app/table/table.component';
import { GpfTableHeaderComponent } from 'app/table/view/header/header.component';
import { GpfTableCellComponent } from 'app/table/view/cell.component';
import { GpfTableEmptyCellComponent } from 'app/table/view/empty-cell.component';
import { GpfTableSubheaderComponent } from 'app/table/component/subheader.component';
import { Column, ColumnGroup, GenotypeBrowser } from 'app/datasets/datasets';
import { GenotypePreview, GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';

describe('GenotypePreviewTableComponent', () => {
  let component: GenotypePreviewTableComponent;
  let fixture: ComponentFixture<GenotypePreviewTableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      schemas: [ CUSTOM_ELEMENTS_SCHEMA ],
      declarations: [
          GenotypePreviewTableComponent,
          GpfTableComponent,
          GpfTableHeaderComponent,
          GpfTableCellComponent,
          GpfTableEmptyCellComponent,
          GpfTableSubheaderComponent
        ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenotypePreviewTableComponent);
    component = fixture.componentInstance;

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
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have working comparator', () => {
    expect(component.comparator('variant.location')).toBe(component.locationComparator);

    expect(component.comparator('field')(
      GenotypePreview.fromJson([null], ['field']),
      GenotypePreview.fromJson([null], ['field'])
    )).toBe(0);

    expect(component.comparator('field')(
      GenotypePreview.fromJson(['value1'], ['field']),
      GenotypePreview.fromJson([null], ['field'])
    )).toBe(1);

    expect(component.comparator('field')(
      GenotypePreview.fromJson([null], ['field']),
      GenotypePreview.fromJson(['value1'], ['field'])
    )).toBe(-1);

    expect(component.comparator('field')(
      GenotypePreview.fromJson([0], ['field']),
      GenotypePreview.fromJson([10], ['field'])
    )).toBe(-10);

    expect(component.locationComparator(
      GenotypePreview.fromJson(['X:123'], ['variant.location']),
      GenotypePreview.fromJson(['1:123'], ['variant.location'])
    )).toBe(99);

    expect(component.locationComparator(
      GenotypePreview.fromJson(['Y:125'], ['variant.location']),
      GenotypePreview.fromJson(['Y:113'], ['variant.location'])
    )).toBe(12);

    expect(component.locationComparator(
      GenotypePreview.fromJson(['Y:125'], ['variant.location']),
      GenotypePreview.fromJson(['M:113'], ['variant.location'])
    )).toBe(-1);
  });

  it('should calculate single column width in onResize()', () => {
    const windowSpy = spyOnProperty(window, 'innerWidth');

    windowSpy.and.returnValue(85);
    component.columns = new Array<Column | ColumnGroup>(1);
    component.onResize();
    expect((component as any).singleColumnWidth).toEqual('10px');

    windowSpy.and.returnValue(2075);
    component.columns = new Array<Column | ColumnGroup>(10);
    component.onResize();
    expect((component as any).singleColumnWidth).toEqual('200px');

    component.columns = new Array<Column | ColumnGroup>(25);
    component.onResize();
    expect((component as any).singleColumnWidth).toEqual('80px');

    windowSpy.and.returnValue(1920);
    component.columns = new Array<Column | ColumnGroup>(12);
    component.onResize();
    expect((component as any).singleColumnWidth).toEqual('153.75px');

    component.columns = new Array<Column | ColumnGroup>(15);
    component.onResize();
    expect((component as any).singleColumnWidth).toEqual('123px');

    windowSpy.and.returnValue(1366);
    component.columns = new Array<Column | ColumnGroup>(8);
    component.onResize();
    expect((component as any).singleColumnWidth).toEqual('161.375px');
   });
});
