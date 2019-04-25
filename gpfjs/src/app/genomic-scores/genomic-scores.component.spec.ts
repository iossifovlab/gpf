import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserDynamicTestingModule } from '@angular/platform-browser-dynamic/testing';
import { FormsModule } from '@angular/forms';

import { NgbModule, NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';

import { MarkdownModule } from 'angular2-markdown';

import { GenomicScoresComponent } from './genomic-scores.component';
import { GenomicScoreState } from './genomic-scores-store';
import { GenomicScores } from 'app/genomic-scores-block/genomic-scores-block';
import { HistogramComponent } from 'app/histogram/histogram.component';
import { HistogramRangeSelectorLineComponent } from 'app/histogram/histogram-range-selector-line.component';
import { PopupComponent } from 'app/popup/popup.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';

describe('GenomicScoresComponent', () => {
  let component: GenomicScoresComponent;
  let fixture: ComponentFixture<GenomicScoresComponent>;
  let modalService: NgbModal;
  let modalRef: NgbModalRef;
  let genomicScoreState: GenomicScoreState;


  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        GenomicScoresComponent,
        HistogramComponent,
        HistogramRangeSelectorLineComponent,
        PopupComponent,
        ErrorsAlertComponent,
      ],
      imports: [
        NgbModule.forRoot(),
        FormsModule,
        MarkdownModule
      ]
    })
    .overrideModule(BrowserDynamicTestingModule, {
      set: {
        entryComponents: [
          PopupComponent
        ]
      }
    })
    .compileComponents();
  }));

  beforeEach(() => {
    modalService = TestBed.get(NgbModal);
    modalRef = modalService.open(PopupComponent);

    fixture = TestBed.createComponent(GenomicScoresComponent);
    component = fixture.componentInstance;

    const genomicScores: GenomicScores = GenomicScores.fromJson({
      bars: [1, 2, 3], score: 'GenomicScores', bins: [4, 5, 6], range: [1, 3],
      desc: 'Genomic Scores description', help: 'gs help', xscale: 'log', yscale: 'linear'
    });
    genomicScoreState = new GenomicScoreState(genomicScores);
    component.genomicScoreState = genomicScoreState;

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show help', () => {
    spyOn(modalService, 'open').and.returnValue(modalRef);
    component.showHelp();
    expect(modalService.open).toHaveBeenCalled();
    expect(modalService.open).toHaveBeenCalledWith(PopupComponent, {
      size: 'lg'
    });
    expect(modalRef.componentInstance.data).toBe('gs help');

    modalRef.close();
  });

  it('should get and set range and domain', () => {
    expect(component.rangeStart).toBe(null);
    expect(component.rangeEnd).toBe(null);
    expect(component.domainMin).toBe(1);
    expect(component.domainMax).toBe(3);

    component.rangeStart = 2;
    component.rangeEnd = 3;
    expect(component.rangeStart).toBe(2);
    expect(component.rangeEnd).toBe(3);

    expect(genomicScoreState.rangeStart).toBe(2);
    expect(genomicScoreState.rangeEnd).toBe(3);
  });

  it('should give selected genomic scores', () => {
    expect(component.selectedGenomicScores.desc).toBe('Genomic Scores description');
  });

  it('should set selected genomic scores', () => {
    const genomicScores: GenomicScores = GenomicScores.fromJson({
      bars: [4, 5, 6], score: 'NewGenomicScores', bins: [7, 8, 9], range: [4, 6],
      desc: 'New Genomic Scores description', help: 'new gs help', xscale: 'linear', yscale: 'log'
    });
    component.selectedGenomicScores = genomicScores;

    expect(component.selectedGenomicScores.desc).toBe('New Genomic Scores description');
  });
});
