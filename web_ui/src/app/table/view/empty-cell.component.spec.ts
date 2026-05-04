import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA, ViewContainerRef } from '@angular/core';

import { GpfTableEmptyCellComponent } from './empty-cell.component';
import { GpfTableColumnComponent } from '../component/column.component';
import { GpfTableContentHeaderComponent } from '../component/header.component';
import { GpfTableContentComponent } from '../component/content.component';
import { ResizeService } from '../resize.service';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';

describe('GpfTableEmptyCellComponent', () => {
  let component: GpfTableEmptyCellComponent;
  let fixture: ComponentFixture<GpfTableEmptyCellComponent>;
  let testComponent: GpfTableColumnComponent;
  let testFixture: ComponentFixture<GpfTableColumnComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        GpfTableEmptyCellComponent,
        GpfTableColumnComponent,
        GenotypePreviewFieldComponent,
        GpfTableContentHeaderComponent,
        GpfTableContentComponent
      ],
      providers: [
        ViewContainerRef,
        ResizeService
      ]
    }).compileComponents();

    testFixture = TestBed.createComponent(GpfTableColumnComponent);
    testComponent = testFixture.componentInstance;
    testFixture.detectChanges();

    fixture = TestBed.createComponent(GpfTableEmptyCellComponent);
    component = fixture.componentInstance;

    component.columnInfo = testComponent;

    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
