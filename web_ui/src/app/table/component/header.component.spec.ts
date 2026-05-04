import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { GpfTableContentHeaderComponent } from './header.component';
import { GpfTableSubheaderComponent } from './subheader.component';

describe('GpfTableContentHeaderComponent', () => {
  let component: GpfTableContentHeaderComponent;
  let fixture: ComponentFixture<GpfTableContentHeaderComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      declarations: [
        GpfTableContentHeaderComponent,
        GpfTableSubheaderComponent
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(GpfTableContentHeaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
