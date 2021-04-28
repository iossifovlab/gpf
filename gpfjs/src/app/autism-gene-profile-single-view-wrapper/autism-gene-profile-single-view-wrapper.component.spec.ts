import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AutismGeneProfileSingleViewWrapperComponent } from './autism-gene-profile-single-view-wrapper.component';

describe('AutismGeneProfileSingleViewWrapperComponent', () => {
  let component: AutismGeneProfileSingleViewWrapperComponent;
  let fixture: ComponentFixture<AutismGeneProfileSingleViewWrapperComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AutismGeneProfileSingleViewWrapperComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneProfileSingleViewWrapperComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
