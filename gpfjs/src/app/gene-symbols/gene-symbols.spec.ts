import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GeneSymbolsComponent } from './gene-symbols.component';
import { Store, StoreModule } from '@ngrx/store';
import { of } from 'rxjs';
import { geneSymbolsReducer, setGeneSymbols } from './gene-symbols.state';
import { APP_BASE_HREF } from '@angular/common';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ConfigService } from 'app/config/config.service';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';

describe('GeneSymbolsComponent', () => {
  let component: GeneSymbolsComponent;
  let fixture: ComponentFixture<GeneSymbolsComponent>;
  let store: Store;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        GeneSymbolsComponent,
        ErrorsAlertComponent
      ],
      providers: [
        ConfigService,
        { provide: APP_BASE_HREF, useValue: '' },
      ],
      imports: [
        StoreModule.forRoot({geneSymbols: geneSymbolsReducer}),
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    fixture = TestBed.createComponent(GeneSymbolsComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of([]));
    jest.spyOn(store, 'dispatch').mockReturnValue();

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get gene symbols from state', () => {
    const setGeneSymbolsSpy = jest.spyOn(component, 'setGeneSymbols');
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    jest.spyOn(store, 'select').mockReturnValueOnce(of(['value1', 'value2']));
    expect(component.geneSymbols.geneSymbols).toBe('');
    component.ngOnInit();

    expect(setGeneSymbolsSpy).toHaveBeenCalledWith('value1\nvalue2');
    expect(component.geneSymbols.geneSymbols).toBe('value1\nvalue2');
    expect(dispatchSpy).toHaveBeenCalledWith(setGeneSymbols({geneSymbols: ['value1', 'value2']}));
  });

  it('should get gene symbols from state when symbols are more than 3', () => {
    const setGeneSymbolsSpy = jest.spyOn(component, 'setGeneSymbols');
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    jest.spyOn(store, 'select').mockReturnValueOnce(of(['value1', 'value2', 'value3', 'value4']));
    expect(component.geneSymbols.geneSymbols).toBe('');
    component.ngOnInit();

    expect(setGeneSymbolsSpy).toHaveBeenCalledWith('value1, value2, value3, value4');
    expect(component.geneSymbols.geneSymbols).toBe('value1, value2, value3, value4');
    expect(dispatchSpy).toHaveBeenCalledWith(setGeneSymbols({geneSymbols: ['value1', 'value2', 'value3', 'value4']}));
  });
});