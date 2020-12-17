import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PhenoToolGenotypeBlockComponent } from './pheno-tool-genotype-block.component';

describe('PhenoToolGenotypeBlockComponent', () => {
  let component: PhenoToolGenotypeBlockComponent;
  let fixture: ComponentFixture<PhenoToolGenotypeBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PhenoToolGenotypeBlockComponent ],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoToolGenotypeBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
