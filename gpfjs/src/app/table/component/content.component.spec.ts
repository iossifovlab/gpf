import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { GpfTableContentComponent } from './content.component';
import { GpfTableSubcontentComponent } from './subcontent.component';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';

describe('GpfTableContentComponent', () => {
  let component: GpfTableContentComponent;
  let fixture: ComponentFixture<GpfTableContentComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        GpfTableContentComponent,
        GenotypePreviewFieldComponent,
        GpfTableSubcontentComponent
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(GpfTableContentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
