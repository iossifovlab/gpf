import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { GpfTableSubheaderComponent } from './subheader.component';
import { GpfTableCellContentDirective } from './content.directive';

describe('GpfTableSubheaderComponent', () => {
  let component: GpfTableSubheaderComponent;
  let fixture: ComponentFixture<GpfTableSubheaderComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        GpfTableSubheaderComponent,
        GpfTableCellContentDirective
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(GpfTableSubheaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
