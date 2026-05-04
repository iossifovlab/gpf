import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA, ViewContainerRef } from '@angular/core';

import { GpfTableHeaderCellComponent } from './header-cell.component';
import { GpfTableContentComponent } from 'app/table/component/content.component';
import { GpfTableContentHeaderComponent } from 'app/table/component/header.component';
import { GenotypePreviewFieldComponent } from 'app/genotype-preview-field/genotype-preview-field.component';
import { GpfTableSubheaderComponent } from 'app/table/component/subheader.component';
import { GpfTableCellContentDirective } from 'app/table/component/content.directive';

describe('GpfTableHeaderCellComponent', () => {
  let component: GpfTableHeaderCellComponent;
  let fixture: ComponentFixture<GpfTableHeaderCellComponent>;
  let testComponent: GpfTableContentHeaderComponent;
  let testFixture: ComponentFixture<GpfTableContentHeaderComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        GpfTableHeaderCellComponent,
        GpfTableContentHeaderComponent,
        GenotypePreviewFieldComponent,
        GpfTableContentComponent,
        GpfTableSubheaderComponent,
        GpfTableCellContentDirective
      ],
      providers: [ViewContainerRef]
    }).compileComponents();

    testFixture = TestBed.createComponent(GpfTableContentHeaderComponent);
    testComponent = testFixture.componentInstance;
    testFixture.detectChanges();

    fixture = TestBed.createComponent(GpfTableHeaderCellComponent);
    component = fixture.componentInstance;

    component.columnInfo = testComponent;

    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
