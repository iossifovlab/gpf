import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GeneSymbolsComponent } from './gene-symbols.component';
import { Store, StoreModule } from '@ngrx/store';
import { Observable, of } from 'rxjs';
import { geneSymbolsReducer, setGeneSymbols } from './gene-symbols.state';
import { APP_BASE_HREF } from '@angular/common';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ConfigService } from 'app/config/config.service';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { provideHttpClient } from '@angular/common/http';
import { GeneService } from 'app/gene-browser/gene.service';
import { resetErrors, setErrors } from 'app/common/errors.state';


class GeneServiceMock {
  public validateGenes(genes: string[]): Observable<string[]> {
    if (genes.includes('invalidGene')) {
      return of(['invalidGene']);
    }
    return of([] as string[]);
  }
}

describe('GeneSymbolsComponent', () => {
  let component: GeneSymbolsComponent;
  let fixture: ComponentFixture<GeneSymbolsComponent>;
  let store: Store;
  const geneServiceMock = new GeneServiceMock();

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        GeneSymbolsComponent,
        ErrorsAlertComponent
      ],
      providers: [
        ConfigService,
        { provide: GeneService, useValue: geneServiceMock },
        { provide: APP_BASE_HREF, useValue: '' },
        provideHttpClient()
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
    jest.spyOn(store, 'dispatch').mockImplementation();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get gene symbols from state', () => {
    const setGeneSymbolsSpy = jest.spyOn(component, 'setGeneSymbols').mockImplementation();
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    jest.spyOn(store, 'select').mockReturnValueOnce(of(['value1', 'value2']));
    expect(component.geneSymbols).toBe('');
    component.ngOnInit();

    expect(component.geneSymbols).toBe('value1\nvalue2');
    expect(setGeneSymbolsSpy).not.toHaveBeenCalledWith();
    expect(dispatchSpy).not.toHaveBeenCalledWith();
  });

  it('should get gene symbols from state when symbols are more than 3', () => {
    const setGeneSymbolsSpy = jest.spyOn(component, 'setGeneSymbols').mockImplementation();
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    jest.spyOn(store, 'select').mockReturnValueOnce(of(['value1', 'value2', 'value3', 'value4']));
    expect(component.geneSymbols).toBe('');
    component.ngOnInit();

    expect(component.geneSymbols).toBe('value1, value2, value3, value4');
    expect(setGeneSymbolsSpy).not.toHaveBeenCalledWith();
    expect(dispatchSpy).not.toHaveBeenCalledWith();
  });

  it('should dispatch to state when genes are valid', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.invalidGenes = 'invlaidGene';
    expect(component.geneSymbols).toBe('');

    const genes = 'CHD8, POGZ, FOXP1';
    component.setGeneSymbols(genes);

    expect(component.geneSymbols).toBe('CHD8, POGZ, FOXP1');
    expect(component.invalidGenes).toBe('');
    expect(dispatchSpy).toHaveBeenCalledWith(setGeneSymbols({geneSymbols: ['CHD8', 'POGZ', 'FOXP1']}));
    expect(dispatchSpy).toHaveBeenCalledWith(resetErrors({componentId: 'geneSymbols'}));
  });

  it('should receive invalid genes list and not dispatch to state', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const genes = 'CHD8, POGZ, FOXP1, invalidGene';
    component.setGeneSymbols(genes);

    expect(component.invalidGenes).toBe('invalidGene');
    expect(component.geneSymbols).toStrictEqual(genes);
    expect(dispatchSpy).not.toHaveBeenCalledWith();
    expect(dispatchSpy).toHaveBeenCalledWith(setErrors({
      errors: {
        componentId: 'geneSymbols', errors: ['Invalid genes: invalidGene']
      }
    }));
  });

  it('should not trigger validate query or save to state when gene symbols are empty', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const validateGenesSpy = jest.spyOn(geneServiceMock, 'validateGenes');
    component.invalidGenes = 'invalidGenes';
    component.geneSymbols = 'CHD8, POGZ, FOXP1';
    component.setGeneSymbols('');

    expect(component.invalidGenes).toBe('');
    expect(component.geneSymbols).toBe('');
    expect(validateGenesSpy).not.toHaveBeenCalledWith();
    expect(dispatchSpy).not.toHaveBeenCalledWith();
  });
});