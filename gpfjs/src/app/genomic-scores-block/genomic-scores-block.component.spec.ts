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
import { StoreModule } from '@ngrx/store';
import { genomicScoresReducer } from './genomic-scores-block.state';
import { GenomicScoresBlockService } from './genomic-scores-block.service';
import { provideHttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { Observable, of } from 'rxjs';

class MockGenomicScoresBlockService {
  public getGenomicScores(): Observable<[]> {
    return of([]);
  }
}

describe('GenomicScoresBlockComponent', () => {
  let component: GenomicScoresBlockComponent;
  let fixture: ComponentFixture<GenomicScoresBlockComponent>;

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
    fixture.detectChanges();
    component.selectedGenomicScores = [];
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
