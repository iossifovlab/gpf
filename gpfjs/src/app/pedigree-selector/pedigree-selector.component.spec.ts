import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { PedigreeSelectorComponent } from './pedigree-selector.component';
import { pedigreeSelectorReducer } from './pedigree-selector.state';
import { StoreModule } from '@ngrx/store';

describe('PedigreeSelectorComponent', () => {
  let component: PedigreeSelectorComponent;
  let fixture: ComponentFixture<PedigreeSelectorComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PedigreeSelectorComponent],
      imports: [StoreModule.forRoot({pedigreeSelector: pedigreeSelectorReducer})],
    }).compileComponents();

    fixture = TestBed.createComponent(PedigreeSelectorComponent);
    component = fixture.componentInstance;
    component.collections = [];
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
