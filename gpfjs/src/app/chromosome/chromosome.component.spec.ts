import { Component, ViewChild } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { ChromosomeComponent } from './chromosome.component';
import { Chromosome } from '../chromosome-service/chromosome';
    

let testChr = Chromosome.fromJson({
  name: '1',
  bands: [
    {start: 0, end: 100, name: 'p6', gieStain: 'gneg'},
    {start: 100, end: 200, name: 'p5', gieStain: 'gpos25'},
    {start: 200, end: 300, name: 'p4', gieStain: 'gpos50'},
    {start: 300, end: 400, name: 'p3', gieStain: 'gpos75'},
    {start: 400, end: 500, name: 'p2', gieStain: 'gpos100'},
    {start: 500, end: 600, name: 'p1', gieStain: 'acen'},
    {start: 600, end: 700, name: 'q1', gieStain: 'acen'},
    {start: 700, end: 900, name: 'q2', gieStain: 'gpos100'},
    {start: 900, end: 1100, name: 'q3', gieStain: 'gpos75'},
    {start: 1100, end: 1300, name: 'q4', gieStain: 'gpos50'},
    {start: 1300, end: 1500, name: 'q5', gieStain: 'gpos25'},
    {start: 1500, end: 1700, name: 'q6', gieStain: 'gneg'},
    {start: 1700, end: 1750, name: 'q7', gieStain: 'stalk'},
    {start: 1750, end: 1800, name: 'q8', gieStain: 'gvar'},
  ],
});


@Component({
  template:
    `<gpf-chromosome #gpfchromosome
      [chromosome]="chr"
      [referenceLargestLength]="1800"
      [centromerePosition]="600"
      [width]="500">
    </gpf-chromosome>`
})
class HostComponent {
  chr = testChr;
  @ViewChild('gpfchromosome') chromEl;
}

describe('ChromosomeComponentBands', () => {
  let component: HostComponent;
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [ NgbModule ],
      declarations: [ HostComponent, ChromosomeComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(HostComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should load all chromosome bands', () => {
    let lBandElems = fixture.debugElement.queryAll((el) => el.nativeElement.id.indexOf('leftBand') != -1);
    let rBandElems = fixture.debugElement.queryAll((el) => el.nativeElement.id.indexOf('rightBand') != -1);
    expect(lBandElems.length).toEqual(6);
    expect(rBandElems.length).toEqual(8);
  });

  it('should properly color chromosome bands', () => {
    let lBandElems = fixture.debugElement.queryAll((el) => el.nativeElement.id.indexOf('leftBand') != -1);
    let rBandElems = fixture.debugElement.queryAll((el) => el.nativeElement.id.indexOf('rightBand') != -1);
    let bandColorsExpected = {
      leftBand1p6: 'rgb(255, 255, 255)',
      leftBand1p5: 'rgb(229, 229, 229)',
      leftBand1p4: 'rgb(179, 179, 179)',
      leftBand1p3: 'rgb(102, 102, 102)',
      leftBand1p2: 'rgb(0, 0, 0)',
      leftBand1p1: 'rgb(139, 35, 35)',
      rightBand1q1: 'rgb(139, 35, 35)',
      rightBand1q2: 'rgb(0, 0, 0)',
      rightBand1q3: 'rgb(102, 102, 102)',
      rightBand1q4: 'rgb(179, 179, 179)',
      rightBand1q5: 'rgb(229, 229, 229)',
      rightBand1q6: 'rgb(255, 255, 255)',
      rightBand1q7: 'rgb(205, 51, 51)',
      rightBand1q8: 'rgb(255, 255, 255)',
    }
    
    for (let band of lBandElems.concat(rBandElems)) {
      expect(band.nativeElement.style.fill).toEqual(bandColorsExpected[band.nativeElement.id]);
    }
  });

  it('should properly position the chromosome bands', () => {
    let lBandElems = fixture.debugElement.queryAll((el) => el.nativeElement.id.indexOf('leftBand') != -1);
    let rBandElems = fixture.debugElement.queryAll((el) => el.nativeElement.id.indexOf('rightBand') != -1);
    let bandElems = lBandElems.concat(rBandElems);
    let bandPositions = new Map<string, any>();
    let bandList = [
      'leftBand1p6', 'leftBand1p5', 'leftBand1p4', 
      'leftBand1p3', 'leftBand1p2', 'leftBand1p1', 
      'rightBand1q1', 'rightBand1q2', 'rightBand1q3', 
      'rightBand1q4', 'rightBand1q5', 'rightBand1q6',
      'rightBand1q7', 'rightBand1q8'
    ];

    for (let band of bandElems) {
      bandPositions[band.nativeElement.id] = {
        x: band.nativeElement.x.baseVal.value,
        y: band.nativeElement.y.baseVal.value,
        width: band.nativeElement.width.baseVal.value,
        height: band.nativeElement.height.baseVal.value,
      };
    }

    expect(bandPositions['rightBand1q6'].width).toEqual(bandPositions['leftBand1p6'].width * 2);
    expect(bandPositions['leftBand1p6'].width).toEqual(bandPositions['rightBand1q8'].width * 2);

    for (let bandNameCurr of bandList) {
      let bandIndex = bandList.indexOf(bandNameCurr);
      if(bandIndex == (bandList.length) - 1) break;
      let bandNameNext = bandList[bandIndex + 1];
      expect(Math.round(bandPositions[bandNameNext].x)).toEqual(Math.round(bandPositions[bandNameCurr].x + bandPositions[bandNameCurr].width));
    }
  });

  it('should add titles to the band elements', () => {
    let lBandElems = fixture.debugElement.queryAll((el) => el.nativeElement.id.indexOf('leftBand') != -1);
    let rBandElems = fixture.debugElement.queryAll((el) => el.nativeElement.id.indexOf('rightBand') != -1);
    let bandElems = lBandElems.concat(rBandElems);
    for (let band of bandElems) {
      expect(band.nativeElement.children.length).toEqual(1);
      expect(band.nativeElement.id.slice(-2)).toEqual(band.nativeElement.children[0].innerHTML);
    }
  });
});


describe('ChromosomeComponentVariants', () => {
  let component: HostComponent ;
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [ NgbModule ],
      declarations: [ 
        HostComponent, ChromosomeComponent
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(HostComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    let gpData: Map<string, any> = new Map([
      ['variant.location', '1:1450'],
      ['effect.worst effect type', 'nonsense'],
      ['genotype.in child', 'prbM'],
      ['effect.genes', 'TESTGENE'],
    ]);

    component.chromEl.genotypePreviews = [gpData];
    component.chromEl.ngOnChanges();
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      expect(component).toBeTruthy();
    });
  });

  xit('should create popovers containing genes and location', () => {
    // TODO
    let gpData: Map<string, any> = new Map([
      ['variant.location', '1:1450'],
      ['effect.worst effect type', 'nonsense'],
      ['genotype.in child', 'prbM'],
      ['effect.genes', 'TESTGENE'],
    ]);

    component.chromEl.genotypePreviews = [gpData];
    component.chromEl.ngOnChanges();
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      console.log('placeholder');
    });
  });

  it('should assign a valid link to the ucsc genome browser', () => {
    let gpData: Map<string, any> = new Map([
      ['variant.location', '1:1450'],
      ['effect.worst effect type', 'nonsense'],
      ['genotype.in child', 'prbM'],
      ['effect.genes', 'TESTGENE'],
    ]);

    component.chromEl.genotypePreviews = [gpData];
    component.chromEl.ngOnChanges();
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      let variantElem = fixture.debugElement.query((el) => el.nativeElement.id.indexOf('variant') != -1);
      expect(variantElem.nativeElement.getAttribute('xlink:href')).toEqual('http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr1:1450-1450');
    });
  });

  it('should determine the max stacking index correctly (probands)', () => {
    let gpData: Map<string, any> = new Map([
      ['variant.location', '1:1450'],
      ['effect.worst effect type', 'nonsense'],
      ['effect.genes', 'TESTGENE'],
    ]);

    let gpDataArr = [];
    ['prbM', 'prbM', 'prbM', 'sibM', 'sibM'].forEach((inChS) => {
      gpDataArr.push(new Map(gpData.set('genotype.in child', inChS)));
    });

    component.chromEl.genotypePreviews = gpDataArr;
    component.chromEl.ngOnChanges();
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      expect(component.chromEl.maxStackIndex).toEqual(3);
    });
  });

  it('should determine the max stacking index correctly (siblings)', () => {
    let gpData: Map<string, any> = new Map([
      ['variant.location', '1:1450'],
      ['effect.worst effect type', 'nonsense'],
      ['effect.genes', 'TESTGENE'],
    ]);

    let gpDataArr = [];
    ['prbM', 'prbM', 'sibM', 'sibM', 'sibM', 'sibM', 'sibM'].forEach((inChS) => {
      gpDataArr.push(new Map(gpData.set('genotype.in child', inChS)));
    });

    component.chromEl.genotypePreviews = gpDataArr;
    component.chromEl.ngOnChanges();
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      expect(component.chromEl.maxStackIndex).toEqual(5);
    });
  });

  it('should draw proband variants on top of the chromosome', () => {
    let gpData: Map<string, any> = new Map([
      ['variant.location', '1:1450'],
      ['genotype.in child', 'prbM'],
      ['effect.worst effect type', 'nonsense'],
      ['effect.genes', 'TESTGENE'],
    ]);
    component.chromEl.genotypePreviews = [gpData];
    component.chromEl.ngOnChanges();
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      let variantBandEl = fixture.debugElement.query((el) => el.nativeElement.id.indexOf('rightBand1q5') != -1);
      let variantElem = fixture.debugElement.query((el) => el.nativeElement.id.indexOf('variant') != -1);
      let figureElem = variantElem.nativeElement.children[0];
      expect(variantBandEl.nativeElement.getBoundingClientRect().y).toBeGreaterThan(figureElem.getBoundingClientRect().y);
    });
  });

  it('should draw sibling variants on bottom of the chromosome', () => {
    let gpData: Map<string, any> = new Map([
      ['variant.location', '1:1450'],
      ['genotype.in child', 'sibM'],
      ['effect.worst effect type', 'nonsense'],
      ['effect.genes', 'TESTGENE'],
    ]);
    component.chromEl.genotypePreviews = [gpData];
    component.chromEl.ngOnChanges();
    fixture.detectChanges();
    fixture.whenStable().then(() => {
      let variantBandEl = fixture.debugElement.query((el) => el.nativeElement.id.indexOf('rightBand1q5') != -1);
      let variantElem = fixture.debugElement.query((el) => el.nativeElement.id.indexOf('variant') != -1);
      let figureElem = variantElem.nativeElement.children[0];
      expect(figureElem.getBoundingClientRect().y).toBeGreaterThan(variantBandEl.nativeElement.getBoundingClientRect().y);
    });
  });

  [ 'nonsense', 'frame-shift', 'splice-site'
  ].forEach((variantType) => {
    it('should assign the star figure to the following variants', async(() => {
      let gpData: Map<string, any> = new Map([
        ['variant.location', '1:1450'],
        ['genotype.in child', 'prbM'],
        ['effect.genes', 'TESTGENE'],
      ]);
      gpData.set('effect.worst effect type', variantType);
      component.chromEl.genotypePreviews = [gpData];
      component.chromEl.ngOnChanges();
      fixture.detectChanges();
      fixture.whenStable().then(() => {
        let variantElem = fixture.debugElement.query((el) => el.nativeElement.id.indexOf('variant') != -1);
        let figureElem = variantElem.nativeElement.children[0];
        expect(figureElem.tagName).toEqual('path');
      });
    }));
  });
  
  ['missense', 'no-frame-shift', 'noStart', 'noEnd',
  ].forEach((variantType) => {
    it('should assign the square figure to the following variants', async(() => {
      let gpData: Map<string, any> = new Map([
        ['variant.location', '1:1450'],
        ['genotype.in child', 'prbM'],
        ['effect.genes', 'TESTGENE'],
      ]);
      gpData.set('effect.worst effect type', variantType);
      component.chromEl.genotypePreviews = [gpData];
      component.chromEl.ngOnChanges();
      fixture.detectChanges();
      fixture.whenStable().then(() => {
        let variantElem = fixture.debugElement.query((el) => el.nativeElement.id.indexOf('variant') != -1);
        let figureElem = variantElem.nativeElement.children[0];
        expect(figureElem.tagName).toEqual('rect');
      });
    }));
  });
  
  ['synonymous', 'non-coding', 'intron', 'intergenic', '3"UTR', '5"UTR',
  ].forEach((variantType) => {
    it('should assign the circle figure to the following variants', async(() => {
      let gpData: Map<string, any> = new Map([
        ['variant.location', '1:1450'],
        ['genotype.in child', 'prbM'],
        ['effect.genes', 'TESTGENE'],
      ]);
      gpData.set('effect.worst effect type', variantType);
      component.chromEl.genotypePreviews = [gpData];
      component.chromEl.ngOnChanges();
      fixture.detectChanges();
      fixture.whenStable().then(() => {
        let variantElem = fixture.debugElement.query((el) => el.nativeElement.id.indexOf('variant') != -1);
        let figureElem = variantElem.nativeElement.children[0];
        expect(figureElem.tagName).toEqual('circle');
      });
    }));
  });

  ['prbM', 'prbF', 'prbU'
  ].forEach((inChS) => {
    it('should assign the correct figures to variants', async(() => {
      let expectedColors = new Map([
        ['prbM', 'blue'],
        ['prbF', 'red'],
        ['prbU', 'green'],
      ]);
      let gpData: Map<string, any> = new Map([
        ['variant.location', '1:1450'],
        ['effect.genes', 'TESTGENE'],
        ['effect.worst effect type', 'nonsense']
      ]);

      gpData.set('genotype.in child', inChS);
      component.chromEl.genotypePreviews = [gpData];
      component.chromEl.ngOnChanges();
      fixture.detectChanges();
      fixture.whenStable().then(() => {
        let variantElem = fixture.debugElement.query((el) => el.nativeElement.id.indexOf('variant') != -1);
        let figureElem = variantElem.nativeElement.children[0];
        expect(figureElem.style.fill).toEqual(expectedColors.get(inChS));
      });
    }));
  });
});
