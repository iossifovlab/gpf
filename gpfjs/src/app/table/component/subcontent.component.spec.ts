import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { Component, NO_ERRORS_SCHEMA } from '@angular/core';
import { GpfTableSubcontentComponent } from './subcontent.component';
import { GpfTableCellContentDirective } from './content.directive';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';

@Component({
  selector: 'gpf-twc',
  template: `
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
  `,
})
class TestWrapperComponent { }

describe('GpfTableSubcontentComponent', () => {
  let component: GpfTableSubcontentComponent;
  let fixture: ComponentFixture<TestWrapperComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        TestWrapperComponent,
        GpfTableSubcontentComponent,
        GenotypePreviewFieldComponent,
        GpfTableCellContentDirective
      ]
    }).compileComponents();
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
    expect(component.contentChildren.length).toBe(2);

    expect(component.contentTemplateRef).toBe(component.contentChildren.first.templateRef);
  });
});
