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
import { provideHttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';

describe('GenesBlockComponent', () => {
  let component: GenesBlockComponent;
  let fixture: ComponentFixture<GenesBlockComponent>;
  let store: Store<State>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [GeneSymbolsComponent, GenesBlockComponent],
      imports: [NgbModule, StoreModule.forRoot({geneSymbols: geneSymbolsReducer}), FormsModule],
      providers: [ConfigService, provideHttpClient()]
    }).compileComponents();

    fixture = TestBed.createComponent(GenesBlockComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of([]));
    jest.spyOn(store, 'dispatch').mockImplementation();

    fixture.detectChanges();

    // Mock ngbNav ViewChild
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    component.ngbNav = {
      activeId: undefined,
      select: jest.fn()
    } as any;
  }));

  afterEach(() => {
    jest.useRealTimers();
  });
  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should open gene symbols tab when loading gene symbols from state', () => {
    jest.useFakeTimers();
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of(['value1', 'value2']));

    component.ngAfterViewInit();
    jest.advanceTimersByTime(100);

    expect(component.ngbNav.select).toHaveBeenCalledWith('geneSymbols');
  });

  it('should open gene sets tab when loading gene sets from state', () => {
    jest.useFakeTimers();
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

    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([[], geneSetsMock, initialGeneScores]));

    component.ngAfterViewInit();
    jest.advanceTimersByTime(100);

    expect(component.ngbNav.select).toHaveBeenCalledWith('geneSets');
  });

  it('should open gene scores tab when loading gene scores from state', () => {
    jest.useFakeTimers();
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

    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([[], initialGeneSets, geneScoresMock]));

    component.ngAfterViewInit();
    jest.advanceTimersByTime(100);

    expect(component.ngbNav.select).toHaveBeenCalledWith('geneScores');
  });

  it('should reset all values when switching tabs', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();
    component.onNavChange();
    expect(dispatchSpy).toHaveBeenCalledWith(resetGeneSymbols());
    expect(dispatchSpy).toHaveBeenCalledWith(resetGeneSetsValues());
    expect(dispatchSpy).toHaveBeenCalledWith(resetGeneScoresValues());
  });
});
