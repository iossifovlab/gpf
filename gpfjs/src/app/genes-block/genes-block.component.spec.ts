import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { of } from 'rxjs';
import { GeneSymbolsComponent } from 'app/gene-symbols/gene-symbols.component';
import { GenesBlockComponent } from './genes-block.component';
import { geneSymbolsReducer, resetGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { FormsModule } from '@angular/forms';
import { StoreModule, Store } from '@ngrx/store';
import { resetGeneSetsValues } from 'app/gene-sets/gene-sets.state';
import { resetGeneScoresValues } from 'app/gene-scores/gene-scores.state';
import { GeneSet, GeneSetsCollection } from 'app/gene-sets/gene-sets';
import { State } from 'app/utils/gpf.state';

describe('GenesBlockComponent', () => {
  let component: GenesBlockComponent;
  let fixture: ComponentFixture<GenesBlockComponent>;
  let store: Store<State>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [GeneSymbolsComponent, GenesBlockComponent],
      imports: [NgbModule, StoreModule.forRoot({geneSymbols: geneSymbolsReducer}), FormsModule],
    }).compileComponents();

    fixture = TestBed.createComponent(GenesBlockComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of([]));
    jest.spyOn(store, 'dispatch').mockReturnValue();

    jest.useFakeTimers();
    const timer: ReturnType<typeof setTimeout> = setTimeout(() => '');
    jest.spyOn(global, 'setTimeout').mockImplementationOnce((fn) => {
      fn();
      return timer;
    });

    fixture.detectChanges();
  }));
  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should open gene symbols tab when loading gene symbols from state', () => {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const rxjs = jest.requireActual('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of(['value1', 'value2']));

    const selectNavSpy = jest.spyOn(component.ngbNav, 'select');

    component.ngAfterViewInit();
    jest.runAllTimers();

    expect(selectNavSpy).toHaveBeenCalledWith('geneSymbols');
    jest.useRealTimers();
  });

  it('should open gene sets tab when loading gene sets from state', () => {
    const geneSetsMock = {
      geneSetsTypes: [],
      geneSetsCollection: new GeneSetsCollection('collection1', 'desc', []),
      geneSet: new GeneSet('set1', 12, 'desc', 'download')
    };

    const initialGeneScores = {
      histogramType: null,
      score: null,
      rangeStart: 0,
      rangeEnd: 0,
      values: null,
      categoricalView: null,
    };

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const rxjs = jest.requireActual('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([[], geneSetsMock, initialGeneScores]));
    const selectNavSpy = jest.spyOn(component.ngbNav, 'select');


    component.ngAfterViewInit();
    jest.runAllTimers();

    expect(selectNavSpy).toHaveBeenCalledWith('geneSets');
    jest.useRealTimers();
  });

  it('should open gene scores tab when loading gene scores from state', () => {
    const initialGeneSets = {
      geneSetsTypes: null,
      geneSetsCollection: null,
      geneSet: null
    };

    const geneScoresMock = {
      histogramType: null,
      score: 'score1',
      rangeStart: 0,
      rangeEnd: 0,
      values: null,
      categoricalView: null,
    };

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const rxjs = jest.requireActual('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([[], initialGeneSets, geneScoresMock]));
    const selectNavSpy = jest.spyOn(component.ngbNav, 'select');


    component.ngAfterViewInit();
    jest.runAllTimers();

    expect(selectNavSpy).toHaveBeenCalledWith('geneScores');
    jest.useRealTimers();
  });

  it('should reset all values when switching tabs', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockReturnValue();
    component.onNavChange();
    expect(dispatchSpy).toHaveBeenCalledWith(resetGeneSymbols());
    expect(dispatchSpy).toHaveBeenCalledWith(resetGeneSetsValues());
    expect(dispatchSpy).toHaveBeenCalledWith(resetGeneScoresValues());
  });
});
