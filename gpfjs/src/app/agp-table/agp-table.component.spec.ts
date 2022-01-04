import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AgpTableComponent } from './agp-table.component';

describe('AgpTableComponent', () => {
  let component: AgpTableComponent;
  let fixture: ComponentFixture<AgpTableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AgpTableComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AgpTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
