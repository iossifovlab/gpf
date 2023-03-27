import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { GpfTableHeaderComponent } from './header.component';
import { GpfTableHeaderCellComponent } from './header-cell.component';
import { GpfTableColumnComponent } from 'app/table/component/column.component';
import { NO_ERRORS_SCHEMA, Component } from '@angular/core';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';
import { GpfTableContentHeaderComponent } from 'app/table/component/header.component';
import { GpfTableContentComponent } from 'app/table/component/content.component';

@Component({
  selector: 'gpf-tgtcc',
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

describe('GpfTableHeaderComponent', () => {
  let component: GpfTableHeaderComponent;
  let fixture: ComponentFixture<GpfTableHeaderComponent>;
  let testComponent: GpfTableColumnComponent;
  let testFixture: ComponentFixture<TestGpfTableColumnComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [ NO_ERRORS_SCHEMA ],
      declarations: [
        GpfTableHeaderComponent,
        GpfTableHeaderCellComponent,
        TestGpfTableColumnComponent,
        GpfTableColumnComponent,
        GenotypePreviewFieldComponent,
        GpfTableContentHeaderComponent,
        GpfTableContentComponent
      ]
    }).compileComponents();

    testFixture = TestBed.createComponent(TestGpfTableColumnComponent);
    testComponent = testFixture.debugElement.children[0].componentInstance;
    testFixture.detectChanges();

    fixture = TestBed.createComponent(GpfTableHeaderComponent);
    component = fixture.componentInstance;

    component.columns = [testComponent];

    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should give sub headers count', () => {
    expect(component.subheadersCount).toStrictEqual([]);
  });

  it('should give column width', () => {
    expect(testComponent.columnWidth).toBe('50.0');
  });
});
