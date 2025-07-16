import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA, ViewContainerRef } from '@angular/core';

import { GpfTableContentComponent } from './content.component';
import { GpfTableContentHeaderComponent } from './header.component';
import { GpfTableColumnComponent } from './column.component';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';

describe('GpfTableColumnComponent', () => {
  let component: GpfTableColumnComponent;
  let fixture: ComponentFixture<GpfTableColumnComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        GpfTableColumnComponent,
        GenotypePreviewFieldComponent,
        GpfTableContentHeaderComponent,
        GpfTableContentComponent
      ],
      providers: [ViewContainerRef]
    }).compileComponents();

    fixture = TestBed.createComponent(GpfTableColumnComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
