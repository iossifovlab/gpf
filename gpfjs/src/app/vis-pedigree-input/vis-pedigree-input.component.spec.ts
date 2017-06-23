import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { VisPedigreeInputComponent } from './vis-pedigree-input.component';

describe('VisPedigreeInputComponent', () => {
  let component: VisPedigreeInputComponent;
  let fixture: ComponentFixture<VisPedigreeInputComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ VisPedigreeInputComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VisPedigreeInputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
