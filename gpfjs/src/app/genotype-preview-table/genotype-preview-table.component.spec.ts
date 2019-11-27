import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';

import { GenotypePreviewTableComponent } from './genotype-preview-table.component';
import { GpfTableComponent } from 'app/table/table.component';
import { GpfTableHeaderComponent } from 'app/table/view/header/header.component';
import { GpfTableCellComponent } from 'app/table/view/cell.component';
import { GpfTableEmptyCellComponent } from 'app/table/view/empty-cell.component';
import { GpfTableSubheaderComponent } from 'app/table/component/subheader.component';
import { AdditionalColumn } from 'app/datasets/datasets';
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

    component.genotypePreviewInfo = {
      columns: ['column1', 'column2'],
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
      maxVariantsCount: 1000
    };
    component.genotypePreviewVariantsArray = new GenotypePreviewVariantsArray();
    component.genotypePreviewVariantsArray.
      addPreviewVariant(['value11', 'value12'], component.genotypePreviewInfo);
    component.genotypePreviewVariantsArray.
      addPreviewVariant(['value21', 'value22'], component.genotypePreviewInfo);
    component.genotypePreviewVariantsArray.
      addPreviewVariant(['value31', 'value32'], component.genotypePreviewInfo);
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
});
