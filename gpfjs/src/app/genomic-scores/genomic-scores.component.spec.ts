import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { BrowserDynamicTestingModule } from '@angular/platform-browser-dynamic/testing';
import { FormsModule } from '@angular/forms';

import { NgbModule, NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';

import { MarkdownModule } from 'ngx-markdown';

import { GenomicScoresComponent } from './genomic-scores.component';
import { GenomicScoreState } from './genomic-scores-store';
import { GenomicScores } from 'app/genomic-scores-block/genomic-scores-block';
import { HistogramComponent } from 'app/histogram/histogram.component';
import { HistogramRangeSelectorLineComponent } from 'app/histogram/histogram-range-selector-line.component';
import { PopupComponent } from 'app/popup/popup.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { Component, ViewChild, NO_ERRORS_SCHEMA } from '@angular/core';

@Component({
  template: `
        <gpf-genomic-scores #genomicscores
          [genomicScoreState]="genomicScoreState"
          [errors]="errors"
          [genomicScoresArray]="genomicScores">
        </gpf-genomic-scores>`
})
class TestHostComponent {

  genomicScores: GenomicScores[] = [
    GenomicScores.fromJson({
      bars: [1, 2, 3], score: 'GenomicScores', bins: [4, 5, 6], range: [1, 3],
      desc: 'Genomic Scores description', help: 'gs help', xscale: 'log', yscale: 'linear'
    })
  ];

  genomicScoreState = new GenomicScoreState(this.genomicScores[0]);

  errors: string[] = [""];

  @ViewChild("genomicscores", {static: true}) genomicScoresComponent: GenomicScoresComponent;
}

describe('GenomicScoresComponent', () => {
  let component: TestHostComponent;
  let fixture: ComponentFixture<TestHostComponent>;
  let modalService: NgbModal;
  let modalRef: NgbModalRef;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        TestHostComponent,
        GenomicScoresComponent,
        PopupComponent,
        ErrorsAlertComponent,
      ],
      imports: [
        NgbModule,
        FormsModule,
        MarkdownModule.forRoot()
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .overrideModule(BrowserDynamicTestingModule, {
      set: {}
    })
    .compileComponents();
  }));


  beforeEach(() => {
    modalService = TestBed.inject(NgbModal);
    modalRef = modalService.open(PopupComponent);

    fixture = TestBed.createComponent(TestHostComponent);
    component = fixture.componentInstance;

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component.genomicScoresComponent).toBeTruthy();
  });

  it('should show help', () => {
    spyOn(modalService, 'open').and.returnValue(modalRef);
    component.genomicScoresComponent.showHelp();
    expect(modalService.open).toHaveBeenCalled();
    expect(modalService.open).toHaveBeenCalledWith(PopupComponent, {
      size: 'lg'
    });
    expect(modalRef.componentInstance.data).toBe('gs help');

    modalRef.close();
  });

  it('should get and set range and domain', () => {
    expect(component.genomicScoresComponent.rangeStart).toBe(null);
    expect(component.genomicScoresComponent.rangeEnd).toBe(null);
    expect(component.genomicScoresComponent.domainMin).toBe(1);
    expect(component.genomicScoresComponent.domainMax).toBe(3);

    component.genomicScoresComponent.rangeStart = 2;
    component.genomicScoresComponent.rangeEnd = 3;
    expect(component.genomicScoresComponent.rangeStart).toBe(2);
    expect(component.genomicScoresComponent.rangeEnd).toBe(3);

  });

  it('should give selected genomic scores', () => {
    expect(component.genomicScoresComponent.selectedGenomicScores.desc).toBe('Genomic Scores description');
  });

  it('should set selected genomic scores', () => {
    const genomicScores: GenomicScores = GenomicScores.fromJson({
      bars: [4, 5, 6], score: 'NewGenomicScores', bins: [7, 8, 9], range: [4, 6],
      desc: 'New Genomic Scores description', help: 'new gs help', xscale: 'linear', yscale: 'log'
    });
    component.genomicScoresComponent.selectedGenomicScores = genomicScores;

    expect(component.genomicScoresComponent.selectedGenomicScores.desc).toBe('New Genomic Scores description');
  });
});
