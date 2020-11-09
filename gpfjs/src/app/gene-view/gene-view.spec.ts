import { GeneViewTranscriptSegment, GeneViewTranscript } from './gene-view';
import { Transcript, Exon } from 'app/gene-view/gene';

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

  it('should calculate isAreaInCDS', () => {
    const exon = new Exon('1', 1, 10);
    const exon1 = new Exon('1', 15, 25);
    const transcript = new Transcript('NM_001130045_1', '+', '1', [100, 200], [exon, exon1]);
    const geneViewTranscript = new GeneViewTranscript(transcript);

    expect(geneViewTranscript.isAreaInCDS(1, 10)).toBe(false);
    expect(geneViewTranscript.isAreaInCDS(120, 180)).toBe(true);
  });

  it('should calculate getCDSTransitionPos', () => {
    const exon = new Exon('1', 1, 10);
    const exon1 = new Exon('1', 80, 110);
    const exon2 = new Exon('1', 120, 180);
    const exon3 = new Exon('1', 190, 250);
    const transcript = new Transcript('NM_001130045_1', '+', '1', [100, 200], [exon, exon1, exon2]);
    const geneViewTranscript = new GeneViewTranscript(transcript);

    expect(geneViewTranscript.getCDSTransitionPos(exon)).toBe(null);
    expect(geneViewTranscript.getCDSTransitionPos(exon1)).toBe(transcript.cds[0]);
    expect(geneViewTranscript.getCDSTransitionPos(exon2)).toBe(null);
    expect(geneViewTranscript.getCDSTransitionPos(exon3)).toBe(transcript.cds[1]);
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
