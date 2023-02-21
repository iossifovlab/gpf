import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { Component, NO_ERRORS_SCHEMA, ViewContainerRef } from '@angular/core';

import { GpfTableContentComponent } from './content.component';
import { GpfTableContentHeaderComponent } from './header.component';
import { GpfTableColumnComponent } from './column.component';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';

@Component({
  selector: 'gpf-twc',
  template: `
    <gpf-table-column columnWidth="50.0">
      <gpf-table-header>
        <gpf-table-subheader caption="caption" field="field">
          <span *gpfTableCellContent="let data">
          </span>
        </gpf-table-subheader>
      </gpf-table-header>
      <gpf-table-content>
        <gpf-table-subcontent [field]="'field'">
          <gpf-genotype-preview-field
            *gpfTableCellContent="let data"
            [field]="'field1'"
            [value]="'value1'"
            [format]="'%s'">
          </gpf-genotype-preview-field>
          <gpf-genotype-preview-field
            *gpfTableCellContent="let data"
            [field]="'field2'"
            [value]="'value2'"
            [format]="'%s'">
          </gpf-genotype-preview-field>
        </gpf-table-subcontent>
      </gpf-table-content>
      <gpf-table-content>
        <gpf-table-subcontent [field]="'field'">
          <gpf-genotype-preview-field
            *gpfTableCellContent="let data"
            [field]="'field1'"
            [value]="'value1'"
            [format]="'%s'">
          </gpf-genotype-preview-field>
          <gpf-genotype-preview-field
            *gpfTableCellContent="let data"
            [field]="'field2'"
            [value]="'value2'"
            [format]="'%s'">
          </gpf-genotype-preview-field>
        </gpf-table-subcontent>
      </gpf-table-content>
    </gpf-table-column>
  `,
})
class TestWrapperComponent { }

describe('GpfTableColumnComponent', () => {
  let component: GpfTableColumnComponent;
  let fixture: ComponentFixture<TestWrapperComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        TestWrapperComponent,
        GpfTableColumnComponent,
        GenotypePreviewFieldComponent,
        GpfTableContentHeaderComponent,
        GpfTableContentComponent
      ],
      providers: [ViewContainerRef]
    }).compileComponents();

    fixture = TestBed.createComponent(TestWrapperComponent);
    component = fixture.debugElement.children[0].componentInstance;
    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should have content children', () => {
    expect(component.headerChildren).toHaveLength(1);
    expect(component.contentChildren).toHaveLength(2);
  });

  it('should have column width', () => {
    expect(component.columnWidth).toBe('50.0');
  });
});
