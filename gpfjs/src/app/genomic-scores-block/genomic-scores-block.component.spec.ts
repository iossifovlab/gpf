import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { MarkdownModule } from 'ngx-markdown';
import { GenomicScoresBlockComponent } from './genomic-scores-block.component';
import { GenomicScoresComponent } from 'app/genomic-scores/genomic-scores.component';
import { PopupComponent } from 'app/popup/popup.component';
import { HistogramComponent } from 'app/histogram/histogram.component';
import { HistogramRangeSelectorLineComponent } from 'app/histogram/histogram-range-selector-line.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { AddButtonComponent } from 'app/add-button/add-button.component';
import { RemoveButtonComponent } from 'app/remove-button/remove-button.component';
import { Store, StoreModule } from '@ngrx/store';
import { genomicScoresReducer, GenomicScoreState, removeGenomicScore } from './genomic-scores-block.state';
import { GenomicScoresBlockService } from './genomic-scores-block.service';
import { provideHttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { Observable, of } from 'rxjs';
import { CategoricalHistogram, GenomicScore, NumberHistogram } from './genomic-scores-block';
import { resetErrors } from 'app/common/errors.state';

class MockGenomicScoresBlockService {
  public getGenomicScores(): Observable<GenomicScore[]> {
    return of([
      new GenomicScore(
        'desc',
        'help',
        'score1',
        new NumberHistogram([1, 2], [4, 5, 6, 7, 8], 'larger1', 'smaller1', 4, 8, true, true)
      ),
      new GenomicScore(
        'desc',
        'help',
        'score2',
        new CategoricalHistogram(
          [
            {name: 'name1', value: 10},
            {name: 'name2', value: 20},
            {name: 'name3', value: 30},
            {name: 'name4', value: 40},
            {name: 'name5', value: 50},
          ],
          ['name1', 'name2', 'name3', 'name4', 'name5'],
          'large value descriptions',
          'small value descriptions',
          true,
        ),
      ),
      new GenomicScore(
        'desc',
        'help',
        'score3',
        new NumberHistogram([1, 2], [9, 10, 11, 12, 13], 'larger1', 'smaller1', 9, 13, true, true)
      ),
      new GenomicScore(
        'desc',
        'help',
        'score4',
        new CategoricalHistogram(
          [
            {name: 'name6', value: 60},
            {name: 'name7', value: 70},
            {name: 'name8', value: 80},
            {name: 'name9', value: 90},
            {name: 'name10', value: 100},
          ],
          ['name6', 'name7', 'name8', 'name9', 'name10'],
          'large value descriptions',
          'small value descriptions',
          true,
        ),
      )
    ]);
  }
}

describe('GenomicScoresBlockComponent', () => {
  let component: GenomicScoresBlockComponent;
  let fixture: ComponentFixture<GenomicScoresBlockComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        GenomicScoresBlockComponent,
        GenomicScoresComponent,
        PopupComponent,
        HistogramComponent,
        HistogramRangeSelectorLineComponent,
        ErrorsAlertComponent,
        AddButtonComponent,
        RemoveButtonComponent,
      ],
      imports: [
        NgbModule,
        FormsModule,
        MarkdownModule,
        StoreModule.forRoot({genomicScores: genomicScoresReducer})
      ],
      providers: [
        { provide: GenomicScoresBlockService, useClass: MockGenomicScoresBlockService },
        provideHttpClient(),
        ConfigService,
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(GenomicScoresBlockComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);

    fixture.detectChanges();
    component.selectedGenomicScores = [];
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should add genomic score and default state for number histogram', () => {
    const addToStateSpy = jest.spyOn(component, 'addToState');
    const score = new GenomicScore(
      'desc',
      'help',
      'score3',
      new NumberHistogram([1, 2], [9, 10, 11, 12, 13], 'larger1', 'smaller1', 9, 13, true, true)
    );

    const state : GenomicScoreState = {
      histogramType: 'continuous',
      score: 'score3',
      rangeStart: 9,
      rangeEnd: 13,
      values: null,
      categoricalView: null,
    };

    component.addFilter(score, 2);

    expect(component.selectedGenomicScores).toStrictEqual([{ score: score, state: state}]);
    expect(component.unusedGenomicScores).toStrictEqual([
      new GenomicScore(
        'desc',
        'help',
        'score1',
        new NumberHistogram([1, 2], [4, 5, 6, 7, 8], 'larger1', 'smaller1', 4, 8, true, true)
      ),
      new GenomicScore(
        'desc',
        'help',
        'score2',
        new CategoricalHistogram(
          [
            {name: 'name1', value: 10},
            {name: 'name2', value: 20},
            {name: 'name3', value: 30},
            {name: 'name4', value: 40},
            {name: 'name5', value: 50},
          ],
          ['name1', 'name2', 'name3', 'name4', 'name5'],
          'large value descriptions',
          'small value descriptions',
          true,
        ),
      ),
      new GenomicScore(
        'desc',
        'help',
        'score4',
        new CategoricalHistogram(
          [
            {name: 'name6', value: 60},
            {name: 'name7', value: 70},
            {name: 'name8', value: 80},
            {name: 'name9', value: 90},
            {name: 'name10', value: 100},
          ],
          ['name6', 'name7', 'name8', 'name9', 'name10'],
          'large value descriptions',
          'small value descriptions',
          true,
        ),
      )
    ]);

    expect(addToStateSpy).toHaveBeenCalledWith(state);
  });

  it('should add genomic score and default state for categorical histogram', () => {
    const addToStateSpy = jest.spyOn(component, 'addToState');
    const score = new GenomicScore(
      'desc',
      'help',
      'score4',
      new CategoricalHistogram(
        [
          {name: 'name6', value: 60},
          {name: 'name7', value: 70},
          {name: 'name8', value: 80},
          {name: 'name9', value: 90},
          {name: 'name10', value: 100},
        ],
        ['name6', 'name7', 'name8', 'name9', 'name10'],
        'large value descriptions',
        'small value descriptions',
        true,
      ),
    );

    const state : GenomicScoreState = {
      histogramType: 'categorical',
      score: 'score4',
      rangeStart: null,
      rangeEnd: null,
      values: ['name6', 'name7', 'name8', 'name9', 'name10'],
      categoricalView: 'range selector',
    };

    component.addFilter(score, 3);

    expect(component.selectedGenomicScores).toStrictEqual([{ score: score, state: state}]);
    expect(component.unusedGenomicScores).toStrictEqual([
      new GenomicScore(
        'desc',
        'help',
        'score1',
        new NumberHistogram([1, 2], [4, 5, 6, 7, 8], 'larger1', 'smaller1', 4, 8, true, true)
      ),
      new GenomicScore(
        'desc',
        'help',
        'score2',
        new CategoricalHistogram(
          [
            {name: 'name1', value: 10},
            {name: 'name2', value: 20},
            {name: 'name3', value: 30},
            {name: 'name4', value: 40},
            {name: 'name5', value: 50},
          ],
          ['name1', 'name2', 'name3', 'name4', 'name5'],
          'large value descriptions',
          'small value descriptions',
          true,
        ),
      ),
      new GenomicScore(
        'desc',
        'help',
        'score3',
        new NumberHistogram([1, 2], [9, 10, 11, 12, 13], 'larger1', 'smaller1', 9, 13, true, true)
      )
    ]);

    expect(addToStateSpy).toHaveBeenCalledWith(state);
  });

  it('should remove genomic score', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const score = new GenomicScore(
      'desc',
      'help',
      'score1',
      new NumberHistogram([1, 2], [4, 5, 6, 7, 8], 'larger1', 'smaller1', 4, 8, true, true)
    );

    const state: GenomicScoreState = {
      histogramType: 'continuous',
      score: 'score1',
      rangeStart: 4,
      rangeEnd: 8,
      values: null,
      categoricalView: null,
    };

    component.selectedGenomicScores = [{ score: score, state: state }];

    component.unusedGenomicScores = [
      new GenomicScore(
        'desc',
        'help',
        'score2',
        new CategoricalHistogram(
          [
            {name: 'name1', value: 10},
            {name: 'name2', value: 20},
            {name: 'name3', value: 30},
            {name: 'name4', value: 40},
            {name: 'name5', value: 50},
          ],
          ['name1', 'name2', 'name3', 'name4', 'name5'],
          'large value descriptions',
          'small value descriptions',
          true,
        ),
      ),
      new GenomicScore(
        'desc',
        'help',
        'score3',
        new NumberHistogram([1, 2], [9, 10, 11, 12, 13], 'larger1', 'smaller1', 9, 13, true, true)
      ),
      new GenomicScore(
        'desc',
        'help',
        'score4',
        new CategoricalHistogram(
          [
            {name: 'name6', value: 60},
            {name: 'name7', value: 70},
            {name: 'name8', value: 80},
            {name: 'name9', value: 90},
            {name: 'name10', value: 100},
          ],
          ['name6', 'name7', 'name8', 'name9', 'name10'],
          'large value descriptions',
          'small value descriptions',
          true,
        ),
      )
    ];

    component.removeFromState(state);

    expect(dispatchSpy).toHaveBeenNthCalledWith(1, removeGenomicScore({
      genomicScoreName: score.score
    }));

    expect(dispatchSpy).toHaveBeenNthCalledWith(2, resetErrors({
      componentId: 'genomicScores: ' + score.score
    }));
  });

  it('should restore state', () => {
    const score = new GenomicScore(
      'desc',
      'help',
      'score1',
      new NumberHistogram([1, 2], [4, 5, 6, 7, 8], 'larger1', 'smaller1', 4, 8, true, true)
    );

    const state: GenomicScoreState = {
      histogramType: 'continuous',
      score: 'score1',
      rangeStart: 4,
      rangeEnd: 8,
      values: null,
      categoricalView: null,
    };

    jest.spyOn(store, 'select').mockReturnValue(of([state]));

    fixture.detectChanges();
    component.ngOnInit();

    expect(component.selectedGenomicScores).toStrictEqual([{ score: score, state: state }]);
    expect(component.unusedGenomicScores).toStrictEqual([
      new GenomicScore(
        'desc',
        'help',
        'score2',
        new CategoricalHistogram(
          [
            {name: 'name1', value: 10},
            {name: 'name2', value: 20},
            {name: 'name3', value: 30},
            {name: 'name4', value: 40},
            {name: 'name5', value: 50},
          ],
          ['name1', 'name2', 'name3', 'name4', 'name5'],
          'large value descriptions',
          'small value descriptions',
          true,
        ),
      ),
      new GenomicScore(
        'desc',
        'help',
        'score3',
        new NumberHistogram([1, 2], [9, 10, 11, 12, 13], 'larger1', 'smaller1', 9, 13, true, true)
      ),
      new GenomicScore(
        'desc',
        'help',
        'score4',
        new CategoricalHistogram(
          [
            {name: 'name6', value: 60},
            {name: 'name7', value: 70},
            {name: 'name8', value: 80},
            {name: 'name9', value: 90},
            {name: 'name10', value: 100},
          ],
          ['name6', 'name7', 'name8', 'name9', 'name10'],
          'large value descriptions',
          'small value descriptions',
          true,
        ),
      )
    ]);
  });
});
