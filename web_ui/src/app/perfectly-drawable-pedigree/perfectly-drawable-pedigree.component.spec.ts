import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { PerfectlyDrawablePedigreeComponent } from './perfectly-drawable-pedigree.component';

describe('PerfectlyDrawablePedigreeComponent', () => {
  let component: PerfectlyDrawablePedigreeComponent;
  let fixture: ComponentFixture<PerfectlyDrawablePedigreeComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PerfectlyDrawablePedigreeComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(PerfectlyDrawablePedigreeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
