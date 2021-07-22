import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { Component, NO_ERRORS_SCHEMA, ViewContainerRef } from '@angular/core';

import { GpfTableEmptyCellComponent } from './empty-cell.component';
import { GpfTableColumnComponent } from '../component/column.component';
import { GpfTableContentHeaderComponent } from '../component/header.component';
import { GpfTableContentComponent } from '../component/content.component';
import { ResizeService } from '../resize.service';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';

@Component({
    selector: 'gpf-tgtcc',
    template: `
      <gpf-table-column>
        <gpf-table-header>
          <gpf-table-subheader caption="caption" field="fieldH">
            <span *gpfTableCellContent="let data">
            </span>
          </gpf-table-subheader>
        </gpf-table-header>
        <gpf-table-content>
          <gpf-table-subcontent [field]="'field'">
            <gpf-genotype-preview-field
              *gpfTableCellContent="let data"
              [field]="'field11'"
              [value]="'value11'"
              [format]="'%s'">
            </gpf-genotype-preview-field>
            <gpf-genotype-preview-field
              *gpfTableCellContent="let data"
              [field]="'field12'"
              [value]="'value12'"
              [format]="'%s'">
            </gpf-genotype-preview-field>
          </gpf-table-subcontent>
        </gpf-table-content>
        <gpf-table-content>
          <gpf-table-subcontent [field]="'field'">
            <gpf-genotype-preview-field
              *gpfTableCellContent="let data"
              [field]="'field21'"
              [value]="'value21'"
              [format]="'%s'">
            </gpf-genotype-preview-field>
            <gpf-genotype-preview-field
              *gpfTableCellContent="let data"
              [field]="'field22'"
              [value]="'value22'"
              [format]="'%s'">
            </gpf-genotype-preview-field>
          </gpf-table-subcontent>
        </gpf-table-content>
      </gpf-table-column>
    `,
  })
  class TestGpfTableColumnComponent { }

describe('GpfTableEmptyCellComponent', () => {
  let component: GpfTableEmptyCellComponent;
  let fixture: ComponentFixture<GpfTableEmptyCellComponent>;
  let testComponent: GpfTableColumnComponent;
  let testFixture: ComponentFixture<TestGpfTableColumnComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [ NO_ERRORS_SCHEMA ],
      declarations: [
        GpfTableEmptyCellComponent,
        TestGpfTableColumnComponent,
        GpfTableColumnComponent,
        GenotypePreviewFieldComponent,
        GpfTableContentHeaderComponent,
        GpfTableContentComponent
      ],
      providers: [
        ViewContainerRef,
        ResizeService
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    testFixture = TestBed.createComponent(TestGpfTableColumnComponent);
    testComponent = testFixture.debugElement.children[0].componentInstance;
    testFixture.detectChanges();

    fixture = TestBed.createComponent(GpfTableEmptyCellComponent);
    component = fixture.componentInstance;

    component.columnInfo = testComponent;

    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should have cell content', () => {
    expect(component.columnInfo.contentChildren.length).toBe(2);
  });

  it('should recalculate width', () => {
    expect(component.columnInfo.columnWidth).toBe('');
    component.recalcWidth();
    expect(component.columnInfo.columnWidth.slice(-2)).toBe('px');
  });
});
