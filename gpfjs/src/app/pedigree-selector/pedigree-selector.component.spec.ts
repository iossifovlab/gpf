import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { PedigreeSelectorComponent } from './pedigree-selector.component';
import { pedigreeSelectorReducer } from './pedigree-selector.state';
import { Store, StoreModule } from '@ngrx/store';
import { of } from 'rxjs';

describe('PedigreeSelectorComponent', () => {
  let component: PedigreeSelectorComponent;
  let fixture: ComponentFixture<PedigreeSelectorComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PedigreeSelectorComponent],
      imports: [StoreModule.forRoot({pedigreeSelector: pedigreeSelectorReducer})],
    }).compileComponents();

    fixture = TestBed.createComponent(PedigreeSelectorComponent);
    component = fixture.componentInstance;
    component.collections = [];

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of({
      id: 'collectionId',
      checkedValues: ['autism']
    }));
    component.collections = [{
      id: 'collectionId',
      name: '',
      domain: [],
    }];

    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
