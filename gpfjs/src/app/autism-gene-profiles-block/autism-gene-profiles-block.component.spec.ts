import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AutismGeneProfilesBlockComponent } from './autism-gene-profiles-block.component';

describe('AutismGeneProfilesBlockComponent', () => {
  let component: AutismGeneProfilesBlockComponent;
  let fixture: ComponentFixture<AutismGeneProfilesBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AutismGeneProfilesBlockComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneProfilesBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
