import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';
import { Observable } from 'rxjs';
import { of } from 'rxjs/internal/observable/of';
import { CategoricalHistogram, CategoricalHistogramView, GeneScore, NumberHistogram } from './gene-scores';
import { GeneScoresComponent } from './gene-scores.component';
import { GeneScoresService } from './gene-scores.service';
import { geneScoresReducer, setGeneScoreCategorical, setGeneScoreContinuous } from './gene-scores.state';
import { Store, StoreModule } from '@ngrx/store';

class MockGeneScoresService {
  public provide = true;
  public getGeneScores(): Observable<GeneScore[]> {
    if (this.provide) {
      return of([
        new GeneScore(
          'desc1',
          'help1',
          'score1',
          new NumberHistogram([1, 2], [4, 5], 'larger1', 'smaller1', 7, 8, true, true),
        ),
        new GeneScore(
          'desc2',
          'help2',
          'score2',
          new NumberHistogram([11, 12], [14, 15], 'larger2', 'smaller2', 17, 88, true, true),
        )
      ]);
    } else {
      return of([] as GeneScore[]);
    }
  }
}
describe('GeneScoresComponent', () => {
  let component: GeneScoresComponent;
  let fixture: ComponentFixture<GeneScoresComponent>;
  let mockGeneScoresService: MockGeneScoresService;
  let store: Store;

  beforeEach(() => {
    mockGeneScoresService = new MockGeneScoresService();

    TestBed.configureTestingModule({
      imports: [
        StoreModule.forRoot({geneScores: geneScoresReducer}), HttpClientTestingModule, NgbNavModule
      ],
      declarations: [GeneScoresComponent],
      providers: [{provide: GeneScoresService, useValue: mockGeneScoresService}, ConfigService],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);

    fixture = TestBed.createComponent(GeneScoresComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should test setting gene scores', () => {
    fixture.detectChanges();
    expect(component.selectedGeneScores.score).toBe('score1');
  });

  it('should test empty gene scores', () => {
    mockGeneScoresService.provide = false;
    fixture.detectChanges();

    expect(fixture.debugElement.query(By.css('div > div.form-block > div.card > ul > li > span'))).toBeTruthy();
    expect(fixture.debugElement.query(By.css('div > div#gene-scores-panel'))).not.toBeTruthy();
  });

  it('should load default score', () => {
    component.ngOnInit();
    expect(component.selectedGeneScores.score).toBe('score1');
  });

  it('should continuous histogram load from state', () => {
    jest.spyOn(store, 'select').mockReturnValue(of({
      histogramType: 'continuous',
      score: 'score2',
      rangeStart: 10,
      rangeEnd: 20,
      values: null,
      categoricalView: null,
    }));

    component.ngOnInit();

    expect(component.selectedGeneScores.score).toBe('score2');
    expect(component.rangeStart).toBe(10);
    expect(component.rangeEnd).toBe(20);
  });

  it('should categorical histogram load from state', () => {
    jest.spyOn(store, 'select').mockReturnValue(of({
      histogramType: 'categorical',
      score: 'score1',
      rangeStart: 10,
      rangeEnd: 20,
      values: ['name2', 'name5'],
      categoricalView: 'click selector',
    }));

    component.ngOnInit();

    expect(component.selectedGeneScores.score).toBe('score1');
    expect(component.categoricalValues).toStrictEqual(['name2', 'name5']);
    expect(component.selectedCategoricalHistogramView).toBe('click selector');
  });

  it('should toggle categorical histogram values and save to state', () => {
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    component.geneScoresLocalState.score = new GeneScore('desc', 'help', 'score1', null);

    const values = ['name5', 'name2'];
    component.categoricalValues = ['name1', 'name2', 'name3'];
    component.toggleCategoricalValues(values);
    expect(dispatchSpy).toHaveBeenCalledWith(setGeneScoreCategorical({
      score: 'score1',
      values: ['name1', 'name3', 'name5'],
      categoricalView: 'range selector',
    }));
  });

  it('should switch categorical histogram view', () => {
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    component.geneScoresLocalState.score = new GeneScore('desc', 'help', 'score1', null);
    component.selectedCategoricalHistogramView = 'range selector';
    component.categoricalValues = ['name1', 'name2', 'name3'];

    component.switchCategoricalHistogramView('click selector' as CategoricalHistogramView);

    expect(component.selectedCategoricalHistogramView).toBe('click selector');
    expect(component.categoricalValues).toStrictEqual([]);

    expect(dispatchSpy).toHaveBeenCalledWith(setGeneScoreCategorical({
      score: 'score1',
      values: [],
      categoricalView: 'click selector',
    }));
  });

  it('should set default categorical histogram view', () => {
    const scoreWithValuesOrder = new GeneScore('desc', 'help', 'score1', new CategoricalHistogram(
      [
        {name: 'name1', value: 10},
        {name: 'name2', value: 20},
        {name: 'name3', value: 30},
      ],
      ['name3', 'name1', 'name2'],
      'large value descriptions',
      'small value descriptions',
      true,
    ));
    component.selectedCategoricalHistogramView = 'range selector';
    component.selectedGeneScores = scoreWithValuesOrder;
    expect(component.selectedCategoricalHistogramView).toBe('range selector');

    const scoreWithoutValuesOrder = new GeneScore('desc', 'help', 'score1', new CategoricalHistogram(
      [
        {name: 'name1', value: 10},
        {name: 'name2', value: 20},
        {name: 'name3', value: 30},
      ],
      null,
      'large value descriptions',
      'small value descriptions',
      true,
    ));
    component.selectedGeneScores = scoreWithoutValuesOrder;
    expect(component.selectedCategoricalHistogramView).toBe('click selector');
  });

  it('should set default ranges for continuous histogram as domain', () => {
    const score = new GeneScore(
      'desc',
      'help',
      'score1',
      new NumberHistogram([1, 2], [4, 5], 'larger1', 'smaller1', null, null, true, true),
    );

    component.selectedGeneScores = score;
    expect(component.geneScoresLocalState.domainMin).toBe(4);
    expect(component.geneScoresLocalState.domainMax).toBe(5);
  });

  it('should set domain using number histogram min and max ranges', () => {
    const score = new GeneScore(
      'desc',
      'help',
      'score1',
      new NumberHistogram([1, 2], [4, 5], 'larger1', 'smaller1', 2, 500, true, true),
    );

    component.selectedGeneScores = score;
    expect(component.geneScoresLocalState.domainMin).toBe(2);
    expect(component.geneScoresLocalState.domainMax).toBe(500);
  });

  it('should set and get range start', () => {
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    const score = new GeneScore(
      'desc',
      'help',
      'score1',
      new NumberHistogram([1, 2], [4, 5], 'larger1', 'smaller1', 2, 500, true, true),
    );

    component.geneScoresLocalState.score = score;
    component.geneScoresLocalState.rangeStart = 0;
    component.geneScoresLocalState.rangeEnd = 10;
    component.rangeStart = 3;

    expect(component.geneScoresLocalState.rangeStart).toBe(3);

    expect(dispatchSpy).toHaveBeenCalledWith(setGeneScoreContinuous({
      score: 'score1',
      rangeStart: 3,
      rangeEnd: 10,
    }));
    expect(component.rangeStart).toBe(3);
  });

  it('should set and get range end', () => {
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    const score = new GeneScore(
      'desc',
      'help',
      'score1',
      new NumberHistogram([1, 2], [4, 5], 'larger1', 'smaller1', 2, 500, true, true),
    );

    component.geneScoresLocalState.score = score;
    component.geneScoresLocalState.rangeStart = 0;
    component.geneScoresLocalState.rangeEnd = 10;
    component.rangeEnd = 3;

    expect(component.geneScoresLocalState.rangeEnd).toBe(3);

    expect(dispatchSpy).toHaveBeenCalledWith(setGeneScoreContinuous({
      score: 'score1',
      rangeStart: 0,
      rangeEnd: 3,
    }));
    expect(component.rangeEnd).toBe(3);
  });
});

