import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserDynamicTestingModule } from '@angular/platform-browser-dynamic/testing';
import { FormsModule } from '@angular/forms';
import { NgbModule, NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { MarkdownModule } from 'ngx-markdown';
import { GenomicScoresComponent } from './genomic-scores.component';
import { GenomicScoreState } from './genomic-scores-store';
import { GenomicScores } from 'app/genomic-scores-block/genomic-scores-block';
import { PopupComponent } from 'app/popup/popup.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('GenomicScoresComponent', () => {
  let component: GenomicScoresComponent;
  let fixture: ComponentFixture<GenomicScoresComponent>;
  let modalService: NgbModal;
  let modalRef: NgbModalRef;

  const initialGenomicScores: GenomicScores[] = [
    GenomicScores.fromJson({
      bars: [1, 2, 3],
      score: 'GenomicScores',
      bins: [4, 5, 6],
      desc: 'Genomic Scores description',
      help: 'gs help',
      xscale: 'log',
      yscale: 'linear'
    })
  ];

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [
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
    modalService = TestBed.inject(NgbModal);
    modalRef = modalService.open(PopupComponent);

    fixture = TestBed.createComponent(GenomicScoresComponent);
    component = fixture.componentInstance;

    component.genomicScoresArray = initialGenomicScores;
    component.genomicScoreState = new GenomicScoreState(initialGenomicScores[0]);
    component.errors = [''];

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show help', () => {
    jest.spyOn(modalService, 'open').mockReturnValue(modalRef);
    component.showHelp();
    expect(modalService.open).toHaveBeenCalledWith(PopupComponent, {
      size: 'lg',
      centered: true
    });
    expect(modalService.open).toHaveBeenCalledWith(PopupComponent, {
      size: 'lg',
      centered: true
    });
    expect((modalRef.componentInstance as PopupComponent).data).toBe('gs help');

    modalRef.close();
  });

  it('should get and set range and domain', () => {
    expect(component.rangeStart).toBeNull();
    expect(component.rangeEnd).toBeNull();
    expect(component.domainMin).toBe(4);
    expect(component.domainMax).toBe(6);

    component.rangeStart = 2;
    component.rangeEnd = 3;
    expect(component.rangeStart).toBe(2);
    expect(component.rangeEnd).toBe(3);
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
