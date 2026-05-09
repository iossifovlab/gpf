import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { GpfTableSubcontentComponent } from './subcontent.component';
import { GpfTableCellContentDirective } from './content.directive';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';

describe('GpfTableSubcontentComponent', () => {
  let component: GpfTableSubcontentComponent;
  let fixture: ComponentFixture<GpfTableSubcontentComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        GpfTableSubcontentComponent,
        GenotypePreviewFieldComponent,
        GpfTableCellContentDirective
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(GpfTableSubcontentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
