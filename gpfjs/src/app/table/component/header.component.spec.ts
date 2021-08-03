import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { Component, NO_ERRORS_SCHEMA } from '@angular/core';

import { GpfTableContentHeaderComponent } from './header.component';
import { GpfTableSubheaderComponent } from './subheader.component';

@Component({
  selector: 'gpf-twc',
  template: `
    <gpf-table-header>
      <gpf-table-subheader caption="caption" field="field">
        <span *gpfTableCellContent="let data">
        </span>
      </gpf-table-subheader>
    </gpf-table-header>
  `,
})
class TestWrapperComponent { }

describe('GpfTableContentHeaderComponent', () => {
  let component: GpfTableContentHeaderComponent;
  let fixture: ComponentFixture<TestWrapperComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [ NO_ERRORS_SCHEMA ],
      declarations: [
        TestWrapperComponent,
        GpfTableContentHeaderComponent,
        GpfTableSubheaderComponent
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
    expect(component.subcolumnsChildren.length).toBe(1);
  });
});
