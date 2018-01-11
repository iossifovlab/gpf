import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChromosomeComponent } from './chromosome.component';

describe('ChromosomeComponent', () => {
  let component: ChromosomeComponent;
  let fixture: ComponentFixture<ChromosomeComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ChromosomeComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ChromosomeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
