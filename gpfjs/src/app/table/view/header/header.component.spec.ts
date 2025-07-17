import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { GpfTableHeaderComponent } from './header.component';
import { GpfTableHeaderCellComponent } from './header-cell.component';
import { GpfTableColumnComponent } from 'app/table/component/column.component';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';
import { GpfTableContentHeaderComponent } from 'app/table/component/header.component';
import { GpfTableContentComponent } from 'app/table/component/content.component';

describe('GpfTableHeaderComponent', () => {
  let component: GpfTableHeaderComponent;
  let fixture: ComponentFixture<GpfTableHeaderComponent>;
  let testComponent: GpfTableColumnComponent;
  let testFixture: ComponentFixture<GpfTableColumnComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        GpfTableHeaderComponent,
        GpfTableHeaderCellComponent,
        GpfTableColumnComponent,
        GenotypePreviewFieldComponent,
        GpfTableContentHeaderComponent,
        GpfTableContentComponent
      ]
    }).compileComponents();

    testFixture = TestBed.createComponent(GpfTableColumnComponent);
    testComponent = testFixture.componentInstance;
    testFixture.detectChanges();

    fixture = TestBed.createComponent(GpfTableHeaderComponent);
    component = fixture.componentInstance;

    component.columns = [testComponent];

    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
