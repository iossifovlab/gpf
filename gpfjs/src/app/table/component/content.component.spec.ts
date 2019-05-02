import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Component, NO_ERRORS_SCHEMA } from '@angular/core';

import { GpfTableContentComponent } from './content.component';
import { GpfTableSubcontentComponent } from './subcontent.component';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';

@Component({
  selector: 'gpf-twc',
  template: `
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
  `,
})
class TestWrapperComponent { }

describe('GpfTableContentComponent', () => {
  let component: GpfTableContentComponent;
  let fixture: ComponentFixture<TestWrapperComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      schemas: [ NO_ERRORS_SCHEMA ],
      declarations: [
        TestWrapperComponent,
        GpfTableContentComponent,
        GenotypePreviewFieldComponent,
        GpfTableSubcontentComponent
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TestWrapperComponent);
    component = fixture.debugElement.children[0].componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should have content children', () => {
    expect(component.subcontentChildren.length).toBe(1);
  });
});
