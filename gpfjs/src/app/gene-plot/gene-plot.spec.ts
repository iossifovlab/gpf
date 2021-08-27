import { Transcript, Exon, Gene, GeneViewTranscriptSegment, GeneViewTranscript } from 'app/gene-view/gene';
import { GeneViewModel } from './gene-view';

describe('GeneViewTranscriptSegment', () => {
  it('should have working getters', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 1109286, 1109306, true, false, false, 'exon 1/16'
    );

    expect(geneViewTranscriptSegment.chrom).toBe('1');
    expect(geneViewTranscriptSegment.start).toBe(1109286);
    expect(geneViewTranscriptSegment.stop).toBe(1109306);
    expect(geneViewTranscriptSegment.isExon).toBe(true);
    expect(geneViewTranscriptSegment.isCDS).toBe(false);
    expect(geneViewTranscriptSegment.isSpacer).toBe(false);
    expect(geneViewTranscriptSegment.label).toBe('exon 1/16');
  });

  it('should calculate length for a spacer segment', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 10, 100, true, false, false, 'exon 1/16'
    );
    expect(geneViewTranscriptSegment.length).toBe(90);
  });

  it('should calculate length for a non spacer segment', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 10, 100, true, false, true, 'exon 1/16'
    );
    expect(geneViewTranscriptSegment.length).toBe(180);
  });

  it('should calculate isIntron when isCDS is false', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 1109286, 1109306, true, false, false, 'exon 1/16'
    );
    expect(geneViewTranscriptSegment.isIntron).toBe(true);
  });

  it('should calculate isIntron when isCDS is true', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 1109286, 1109306, true, true, false, 'exon 1/16'
    );
    expect(geneViewTranscriptSegment.isIntron).toBe(false);
  });

  it('should calculate intersectionLength', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 10, 100, true, false, false, 'exon 1/16'
    );
    expect(geneViewTranscriptSegment.intersectionLength(5, 105)).toBe(90);
    expect(geneViewTranscriptSegment.intersectionLength(100, 10)).toBe(0);
  });

  it('should calculate isSubSegment', () => {
    const geneViewTranscriptSegment = new GeneViewTranscriptSegment(
      '1', 10, 100, true, false, false, 'exon 1/16'
    );
    expect(geneViewTranscriptSegment.isSubSegment(5, 105)).toBe(true);
    expect(geneViewTranscriptSegment.isSubSegment(100, 10)).toBe(false);
  });
});

describe('GeneViewTranscript', () => {
  it('should have working getters', () => {
    const exon = new Exon('1', 1, 10);
    const exon1 = new Exon('1', 15, 25);
    const transcript = new Transcript('NM_001130045_1', '+', '1', [100, 200], [exon, exon1]);
    const geneViewTranscript = new GeneViewTranscript(transcript);

    expect(geneViewTranscript.start).toBe(transcript.start);
    expect(geneViewTranscript.stop).toBe(transcript.stop);
    expect(geneViewTranscript.strand).toBe(transcript.strand);
  });

  it('should calculate resolveRegionChromosomes', () => {
    const exon = new Exon('1', 1, 10);
    const exon1 = new Exon('2', 15, 25);
    const exon2 = new Exon('3', 40, 55);
    const exon3 = new Exon('4', 80, 100);
    const transcript = new Transcript('NM_001130045_1', '+', '1', [100, 200], [exon, exon1, exon2, exon3]);
    const geneViewTranscript = new GeneViewTranscript(transcript);

    expect(geneViewTranscript.resolveRegionChromosomes([1, 10])).toEqual(['1:1-10']);
    expect(geneViewTranscript.resolveRegionChromosomes([1, 35])).toEqual(['1:1-10', '2:15-25']);
    expect(geneViewTranscript.resolveRegionChromosomes([10, 60])).toEqual(['2:15-25', '3:40-55']);
    expect(geneViewTranscript.resolveRegionChromosomes([1, 120])).toEqual(['1:1-10', '2:15-25', '3:40-55', '4:80-100']);
  });
});

describe('GeneViewModel', () => {
  it('should have working getters', () => {
    const exon = new Exon('1', 1, 10);
    const exon1 = new Exon('1', 15, 25);
    const exon2 = new Exon('1', 30, 40);
    const exon3 = new Exon('1', 45, 55);
    const transcript = new Transcript('NM_001130045_1', '+', '1', [100, 200], [exon, exon1]);
    const transcript1 = new Transcript('NM_001130045_2', '+', '1', [100, 200], [exon2, exon3]);
    const gene = new Gene('TEST', [transcript, transcript1]);
    const geneViewModel = new GeneViewModel(gene, 1500);


    expect(geneViewModel.gene).toBe(gene);
  });

  it('should calculate buildDomain', () => {
    const exon = new Exon('1', 1, 10);
    const exon1 = new Exon('1', 15, 25);
    const exon2 = new Exon('1', 30, 40);
    const exon3 = new Exon('1', 45, 55);
    const transcript = new Transcript('NM_001130045_1', '+', '1', [100, 200], [exon, exon1]);
    const transcript1 = new Transcript('NM_001130045_2', '+', '1', [100, 200], [exon2, exon3]);
    const gene = new Gene('TEST', [transcript, transcript1]);
    const geneViewModel = new GeneViewModel(gene, 1500);

    expect(geneViewModel.buildDomain(0, 3000000000)).toEqual([1, 10, 15, 25, 30, 40, 45, 55]);
    expect(geneViewModel.buildDomain(0, 10)).toEqual([1, 10]);
    expect(geneViewModel.buildDomain(0, 5)).toEqual([0, 5]);
  });

  it('should calculate buildRange without spacer segments', () => {
    const exon = new Exon('1', 1, 10);
    const exon1 = new Exon('1', 15, 25);
    const exon2 = new Exon('1', 30, 40);
    const exon3 = new Exon('1', 45, 55);
    const transcript = new Transcript('NM_001130045_1', '+', '1', [100, 200], [exon, exon1]);
    const transcript1 = new Transcript('NM_001130045_2', '+', '1', [100, 200], [exon2, exon3]);
    const gene = new Gene('TEST', [transcript, transcript1]);
    const geneViewModel = new GeneViewModel(gene, 1500);

    expect(geneViewModel.buildRange(0, 3000000000, 1500, false)).toEqual(
      [0, 250, 388.8888888888889, 666.6666666666667, 805.5555555555557, 1083.3333333333335, 1222.2222222222224, 1500.0000000000002]
    );
    expect(geneViewModel.buildRange(0, 3000000000, 1500, true)).toEqual(
      [0, 214.28571428571428, 428.57142857142856, 642.8571428571429, 857.1428571428571, 1071.4285714285713, 1285.7142857142856, 1499.9999999999998]
    );
  });

  it('should calculate buildRange with spacer segments', () => {
    const exon = new Exon('1', 1, 10);
    const exon1 = new Exon('1', 15, 25);
    const exon2 = new Exon('2', 30, 40);
    const exon3 = new Exon('2', 45, 55);
    const transcript = new Transcript('NM_001130045_1', '+', '1', [100, 200], [exon, exon1]);
    const transcript1 = new Transcript('NM_001130045_2', '+', '1', [100, 200], [exon2, exon3]);
    const gene = new Gene('TEST1', [transcript, transcript1]);
    const geneViewModel = new GeneViewModel(gene, 1500);

    expect(geneViewModel.buildRange(0, 3000000000, 1500, true)).toEqual(
      [0, 225, 450, 675, 825, 1050, 1275, 1500]
    );
  });
});
