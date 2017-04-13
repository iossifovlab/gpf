import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PhenoToolComponent } from './pheno-tool.component';

describe('PhenoToolComponent', () => {
  let component: PhenoToolComponent;
  let fixture: ComponentFixture<PhenoToolComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoToolComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoToolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
