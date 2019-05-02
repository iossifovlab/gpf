import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';

import { GenotypePreviewTableComponent } from './genotype-preview-table.component';
import { GpfTableComponent } from 'app/table/table.component';
import { GpfTableHeaderComponent } from 'app/table/view/header/header.component';
import { GpfTableCellComponent } from 'app/table/view/cell.component';
import { GpfTableEmptyCellComponent } from 'app/table/view/empty-cell.component';
import { GpfTableSubheaderComponent } from 'app/table/component/subheader.component';
import { AdditionalColumn } from 'app/datasets/datasets';
import { GenotypePreview } from 'app/genotype-preview-model/genotype-preview';

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

    component.genotypePreviewsArray = {
      genotypePreviews: [
        GenotypePreview.fromJson('0', {rows: [['value11', 'value12']], cols: ['column1', 'column2']}),
        GenotypePreview.fromJson('0', {rows: [['value21', 'value22']], cols: ['column1', 'column2']}),
        GenotypePreview.fromJson('0', {rows: [['value31', 'value32']], cols: ['column1', 'column2']}),
      ],
      legend: [
        {
          color: '#E35252',
          id: 'id1',
          name: 'name1'
        },
        {
          color: '#AAAAAA',
          id: 'id2',
          name: 'name2'
        }
      ],
      total: 3
    };
    component.columns = AdditionalColumn.fromJsonArray([
      {
        id: 'column1',
        name: 'column1',
        source: 'column1',
        slots: [
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
        slots: [ ]
      }
    ]);

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have working comparator', () => {
    expect(component.comparator('location')).toBe(component.locationComparator);

    expect(component.comparator('field')(
      GenotypePreview.fromJson('0', {rows: [[null]], cols: ['field']}),
      GenotypePreview.fromJson('0', {rows: [[null]], cols: ['field']})
    )).toBe(0);

    expect(component.comparator('field')(
      GenotypePreview.fromJson('0', {rows: [['value1']], cols: ['field']}),
      GenotypePreview.fromJson('0', {rows: [[null]], cols: ['field']})
    )).toBe(1);

    expect(component.comparator('field')(
      GenotypePreview.fromJson('0', {rows: [[null]], cols: ['field']}),
      GenotypePreview.fromJson('0', {rows: [['value1']], cols: ['field']})
    )).toBe(-1);

    expect(component.comparator('field')(
      GenotypePreview.fromJson('0', {rows: [[[0]]], cols: ['field']}),
      GenotypePreview.fromJson('0', {rows: [[[10]]], cols: ['field']})
    )).toBe(-10);

    expect(component.locationComparator(
      GenotypePreview.fromJson('0', {rows: [['X:123']], cols: ['location']}),
      GenotypePreview.fromJson('0', {rows: [['1:123']], cols: ['location']})
    )).toBe(99);

    expect(component.locationComparator(
      GenotypePreview.fromJson('0', {rows: [['Y:125']], cols: ['location']}),
      GenotypePreview.fromJson('0', {rows: [['Y:113']], cols: ['location']})
    )).toBe(12);

    expect(component.locationComparator(
      GenotypePreview.fromJson('0', {rows: [['Y:125']], cols: ['location']}),
      GenotypePreview.fromJson('0', {rows: [['M:113']], cols: ['location']})
    )).toBe(-1);
  });
});
