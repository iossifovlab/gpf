import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { of } from 'rxjs';
import { GeneSymbolsComponent } from 'app/gene-symbols/gene-symbols.component';
import { GenesBlockComponent } from './genes-block.component';
import { geneSymbolsReducer } from 'app/gene-symbols/gene-symbols.state';
import { FormsModule } from '@angular/forms';
import { StoreModule, Store } from '@ngrx/store';

describe('GenesBlockComponent', () => {
  let component: GenesBlockComponent;
  let fixture: ComponentFixture<GenesBlockComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [GeneSymbolsComponent, GenesBlockComponent],
      imports: [NgbModule, StoreModule.forRoot({geneSymbols: geneSymbolsReducer}), FormsModule],
    }).compileComponents();
    fixture = TestBed.createComponent(GenesBlockComponent);
    component = fixture.componentInstance;

    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of(['value1', 'value2']));
    jest.spyOn(store, 'dispatch').mockReturnValue();

    fixture.detectChanges();
  }));
  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
