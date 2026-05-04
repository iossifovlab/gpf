import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { Component, NO_ERRORS_SCHEMA, ViewContainerRef } from '@angular/core';

import { GpfTableCellComponent } from './cell.component';
import { GpfTableColumnComponent } from '../component/column.component';
import { GpfTableContentHeaderComponent } from '../component/header.component';
import { GpfTableContentComponent } from '../component/content.component';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';

@Component({
  selector: 'gpf-tgtcc',
  standalone: false,
  template: `
    <gpf-table-column columnWidth="50.0">
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

describe('GpfTableCellComponent', () => {
  let component: GpfTableCellComponent;
  let fixture: ComponentFixture<GpfTableCellComponent>;
  let testComponent: GpfTableColumnComponent;
  let testFixture: ComponentFixture<TestGpfTableColumnComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        GpfTableCellComponent,
        TestGpfTableColumnComponent,
        GpfTableColumnComponent,
        GenotypePreviewFieldComponent,
        GpfTableContentHeaderComponent,
        GpfTableContentComponent
      ],
      providers: [ViewContainerRef]
    }).compileComponents();

    testFixture = TestBed.createComponent(TestGpfTableColumnComponent);
    testComponent = testFixture.debugElement.children[0].componentInstance;
    testFixture.detectChanges();

    fixture = TestBed.createComponent(GpfTableCellComponent);
    component = fixture.componentInstance;

    component.columnInfo = testComponent;
    component.data = {fieldH: 'valueH', field11: 'value11', field12: 'value12', field21: 'value21', field22: 'value22'};
    component.noScrollOptimization = false;

    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should give cell content', () => {
    expect(component.columnInfo.contentChildren).toHaveLength(2);
    expect(component.columnInfo.contentChildren).toHaveLength(testComponent.contentChildren.length);

    expect(component.cellContent).toBe(testComponent.contentChildren.first);
  });
});
