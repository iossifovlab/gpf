import { CNV, CODING, LGDS, OTHER } from 'app/effect-types/effect-types';
import { SummaryAllele, SummaryAllelesArray, SummaryAllelesFilter } from './summary-variants';

describe('SummaryAllele', () => {
  it('should create from row', () => {
    const a = new SummaryAllele();
    const aComparisonValue = spyOnProperty(a, 'comparisonValue');
    const b = new SummaryAllele();
    const bComparisonValue = spyOnProperty(b, 'comparisonValue');

    aComparisonValue.and.returnValue(1);
    bComparisonValue.and.returnValue(0);
    expect(SummaryAllele.comparator(a, b)).toBe(1);
    aComparisonValue.and.returnValue(0);
    bComparisonValue.and.returnValue(1);
    expect(SummaryAllele.comparator(a, b)).toBe(-1);
    aComparisonValue.and.returnValue(1);
    bComparisonValue.and.returnValue(1);
    expect(SummaryAllele.comparator(a, b)).toBe(0);
    aComparisonValue.and.returnValue(0);
    bComparisonValue.and.returnValue(0);
    expect(SummaryAllele.comparator(a, b)).toBe(0);
  });

  it('should create from row', () => {
    let summaryAllele;
    const row = {
      location: 'location1',
      position: 3,
      end_position: 7,
      chrom: 'chrom1',
      variant: 'variant1',
      effect: 'effect1',
      frequency: 13,
      family_variants_count: 17,
      is_denovo: true,
      seen_in_affected: false,
      seen_in_unaffected: true,
    };
    summaryAllele = SummaryAllele.fromRow(row);

    expect(summaryAllele.location).toEqual('location1');
    expect(summaryAllele.position).toEqual(3);
    expect(summaryAllele.endPosition).toEqual(7);
    expect(summaryAllele.chrom).toEqual('chrom1');
    expect(summaryAllele.variant).toEqual('variant1');
    expect(summaryAllele.effect).toEqual('effect1');
    expect(summaryAllele.frequency).toEqual(13);
    expect(summaryAllele.numberOfFamilyVariants).toEqual(17);
    expect(summaryAllele.seenAsDenovo).toEqual(true);
    expect(summaryAllele.seenInAffected).toEqual(false);
    expect(summaryAllele.seenInUnaffected).toEqual(true);
    expect(summaryAllele.sauid).toEqual(row.location + ':' + row.variant);
    expect(summaryAllele.svuid).toEqual(row.location + ':' + row.variant);

    row.is_denovo = false;
    row.seen_in_affected = true;
    row.seen_in_unaffected = false;
    summaryAllele = SummaryAllele.fromRow(row, 'svuid1');
    expect(summaryAllele.seenAsDenovo).toEqual(false);
    expect(summaryAllele.seenInAffected).toEqual(true);
    expect(summaryAllele.seenInUnaffected).toEqual(false);
    expect(summaryAllele.sauid).toEqual(row.location + ':' + row.variant);
    expect(summaryAllele.svuid).toEqual('svuid1');
  });

  it('should get affected status', () => {
    const summaryAllele = new SummaryAllele();

    summaryAllele.seenInAffected = true;
    summaryAllele.seenInUnaffected = true;
    expect(summaryAllele.affectedStatus).toEqual('Affected and unaffected');

    summaryAllele.seenInAffected = true;
    summaryAllele.seenInUnaffected = false;
    expect(summaryAllele.affectedStatus).toEqual('Affected only');

    summaryAllele.seenInAffected = false;
    summaryAllele.seenInUnaffected = true;
    expect(summaryAllele.affectedStatus).toEqual('Unaffected only');
  });

  it('should get variant type', () => {
    const summaryAllele = new SummaryAllele();

    summaryAllele.variant = 'sub???';
    expect(summaryAllele.variantType).toEqual('sub');
    summaryAllele.variant = 'ins???';
    expect(summaryAllele.variantType).toEqual('ins');
    summaryAllele.variant = 'CNV+???';
    summaryAllele.effect = 'CNV+';
    expect(summaryAllele.variantType).toEqual('CNV+');
    summaryAllele.variant = 'CNV-???';
    summaryAllele.effect = 'CNV-';
    expect(summaryAllele.variantType).toEqual('CNV-');
  });

  it('should check is lgds', () => {
    const summaryAllele = new SummaryAllele();

    summaryAllele.effect = 'lgds';
    expect(summaryAllele.isLGDs()).toBeTrue();
    summaryAllele.effect = 'nonsense';
    expect(summaryAllele.isLGDs()).toBeTrue();
    summaryAllele.effect = '';
    expect(summaryAllele.isLGDs()).toBeFalse();
  });

  it('should check is missense', () => {
    const summaryAllele = new SummaryAllele();

    summaryAllele.effect = 'missense';
    expect(summaryAllele.isMissense()).toBeTrue();
    summaryAllele.effect = '';
    expect(summaryAllele.isMissense()).toBeFalse();
  });

  it('should check is synonymous', () => {
    const summaryAllele = new SummaryAllele();

    summaryAllele.effect = 'synonymous';
    expect(summaryAllele.isSynonymous()).toBeTrue();
    summaryAllele.effect = '';
    expect(summaryAllele.isSynonymous()).toBeFalse();
  });

  it('should check is CNV+', () => {
    const summaryAllele = new SummaryAllele();

    summaryAllele.effect = 'CNV+';
    expect(summaryAllele.isCNVPlus()).toBeTrue();
    summaryAllele.effect = '';
    expect(summaryAllele.isCNVPlus()).toBeFalse();
  });

  it('should check is CNV-', () => {
    const summaryAllele = new SummaryAllele();

    summaryAllele.effect = 'CNV-';
    expect(summaryAllele.isCNVMinus()).toBeTrue();
    summaryAllele.effect = '';
    expect(summaryAllele.isCNVMinus()).toBeFalse();
  });

  it('should check is CNV', () => {
    const summaryAllele = new SummaryAllele();

    summaryAllele.effect = 'CNV+';
    expect(summaryAllele.isCNV()).toBeTrue();
    summaryAllele.effect = 'CNV-';
    expect(summaryAllele.isCNV()).toBeTrue();
    summaryAllele.effect = '';
    expect(summaryAllele.isCNV()).toBeFalse();
  });

  it('should get comparison value', () => {
    const summaryAllele1 = new SummaryAllele();
    summaryAllele1.seenAsDenovo = false;
    summaryAllele1.effect = 'CNV+';
    summaryAllele1.seenInAffected = true;
    summaryAllele1.seenInUnaffected = true;

    const summaryAllele2 = new SummaryAllele();
    summaryAllele2.seenAsDenovo = false;
    summaryAllele2.effect = 'CNV+';
    summaryAllele2.seenInAffected = false;
    summaryAllele2.seenInUnaffected = true;

    const summaryAllele3 = new SummaryAllele();
    summaryAllele3.seenAsDenovo = false;
    summaryAllele3.effect = 'CNV+';
    summaryAllele3.seenInAffected = true;
    summaryAllele3.seenInUnaffected = false;

    const summaryAllele4 = new SummaryAllele();
    summaryAllele4.seenAsDenovo = true;
    summaryAllele4.effect = 'CNV+';

    const summaryAllele5 = new SummaryAllele();
    summaryAllele5.seenAsDenovo = false;
    summaryAllele5.effect = 'intron';

    const summaryAllele6 = new SummaryAllele();
    summaryAllele6.seenAsDenovo = false;
    summaryAllele6.effect = 'synonymous';

    const summaryAllele7 = new SummaryAllele();
    summaryAllele7.seenAsDenovo = false;
    summaryAllele7.effect = 'missense';

    const summaryAllele8 = new SummaryAllele();
    summaryAllele8.seenAsDenovo = false;
    summaryAllele8.effect = 'lgds';

    const summaryAllele9 = new SummaryAllele();
    summaryAllele9.seenAsDenovo = true;
    summaryAllele9.effect = 'lgds';

    expect(summaryAllele1.comparisonValue < summaryAllele2.comparisonValue).toBeTrue();
    expect(summaryAllele2.comparisonValue < summaryAllele3.comparisonValue).toBeTrue();
    expect(summaryAllele3.comparisonValue < summaryAllele4.comparisonValue).toBeTrue();
    expect(summaryAllele4.comparisonValue < summaryAllele5.comparisonValue).toBeTrue();
    expect(summaryAllele5.comparisonValue < summaryAllele6.comparisonValue).toBeTrue();
    expect(summaryAllele6.comparisonValue < summaryAllele7.comparisonValue).toBeTrue();
    expect(summaryAllele7.comparisonValue < summaryAllele8.comparisonValue).toBeTrue();
    expect(summaryAllele8.comparisonValue < summaryAllele9.comparisonValue).toBeTrue();
  });

  it('should check if intersects', () => {
    const summaryAllele1 = new SummaryAllele();
    const summaryAllele2 = new SummaryAllele();

    summaryAllele1.effect = 'lgds';
    summaryAllele1.position = 13;
    summaryAllele2.effect = 'lgds';
    summaryAllele2.position = 13;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeTrue();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeTrue();
    summaryAllele1.position = 13;
    summaryAllele2.position = 14;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeFalse();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeFalse();

    summaryAllele1.effect = 'CNV+';
    summaryAllele1.position = 13;
    summaryAllele1.endPosition = 17;
    summaryAllele2.effect = 'CNV-';
    summaryAllele2.position = 3;
    summaryAllele2.endPosition = 15;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeTrue();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeTrue();
    summaryAllele1.position = 13;
    summaryAllele1.endPosition = 17;
    summaryAllele2.position = 14;
    summaryAllele2.endPosition = 23;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeTrue();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeTrue();
    summaryAllele1.position = 13;
    summaryAllele1.endPosition = 17;
    summaryAllele2.position = 18;
    summaryAllele2.endPosition = 23;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeFalse();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeFalse();
    summaryAllele1.position = 13;
    summaryAllele1.endPosition = 17;
    summaryAllele2.position = 1;
    summaryAllele2.endPosition = 12;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeFalse();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeFalse();

    summaryAllele1.effect = 'lgds';
    summaryAllele1.position = 13;
    summaryAllele2.effect = 'CNV+';
    summaryAllele2.position = 3;
    summaryAllele2.endPosition = 15;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeTrue();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeTrue();
    summaryAllele1.position = 13;
    summaryAllele2.position = 14;
    summaryAllele2.endPosition = 15;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeFalse();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeFalse();
    summaryAllele1.position = 13;
    summaryAllele2.position = 3;
    summaryAllele2.endPosition = 12;
    expect(summaryAllele1.intersects(summaryAllele2)).toBeFalse();
    expect(summaryAllele2.intersects(summaryAllele1)).toBeFalse();
  });
});

describe('SummaryAllelesArray', () => {
  it('should add summary row', () => {
    const row = {
      alleles: [
        {
          location: 'location1',
          position: 3,
          end_position: 7,
          chrom: 'chrom1',
          variant: 'variant1',
          effect: 'effect1',
          frequency: 13,
          family_variants_count: 17,
          is_denovo: true,
          seen_in_affected: false,
          seen_in_unaffected: true,
        },
        {
          location: 'location2',
          position: 4,
          end_position: 9,
          chrom: 'chrom2',
          variant: 'variant2',
          effect: 'effect2',
          frequency: 14,
          family_variants_count: 16,
          is_denovo: false,
          seen_in_affected: false,
          seen_in_unaffected: false,
        }
      ]
    };
    const summaryAlleleArray = new SummaryAllelesArray();
    summaryAlleleArray.addSummaryRow(row);
    expect(summaryAlleleArray.summaryAlleles).toEqual([
      SummaryAllele.fromRow(row.alleles[0]),
      SummaryAllele.fromRow(row.alleles[1])
    ]);
  });

  it('should add summary allele', () => {
    const summaryAllele1 = new SummaryAllele();
    summaryAllele1.numberOfFamilyVariants = 3;
    summaryAllele1.seenAsDenovo = false;
    summaryAllele1.seenInAffected = true;
    summaryAllele1.seenInUnaffected = false;
    summaryAllele1.sauid = 'sauid1';

    const summaryAllele2 = new SummaryAllele();
    summaryAllele2.numberOfFamilyVariants = 13;
    summaryAllele2.seenAsDenovo = true;
    summaryAllele2.seenInAffected = false;
    summaryAllele2.seenInUnaffected = true;
    summaryAllele2.sauid = 'sauid2';

    const summaryAllele3 = new SummaryAllele();
    summaryAllele3.numberOfFamilyVariants = 7;
    summaryAllele3.seenAsDenovo = true;
    summaryAllele3.seenInAffected = false;
    summaryAllele3.seenInUnaffected = false;
    summaryAllele3.sauid = 'sauid1';

    const summaryAlleleArray = new SummaryAllelesArray();

    summaryAlleleArray.addSummaryAllele(summaryAllele1);
    summaryAlleleArray.addSummaryAllele(summaryAllele2);
    expect(summaryAlleleArray.summaryAlleles).toEqual([summaryAllele1, summaryAllele2]);
    expect(summaryAlleleArray.summaryAlleleIds).toEqual(['sauid1', 'sauid2']);

    summaryAlleleArray.addSummaryAllele(summaryAllele3);
    expect(summaryAlleleArray.summaryAlleles[0].sauid).toEqual('sauid1');
    expect(summaryAlleleArray.summaryAlleles[0].numberOfFamilyVariants).toEqual(10);
    expect(summaryAlleleArray.summaryAlleles[0].seenAsDenovo).toBeTrue();
    expect(summaryAlleleArray.summaryAlleles[0].seenInAffected).toBeTrue();
    expect(summaryAlleleArray.summaryAlleles[0].seenInUnaffected).toBeFalse();
    expect(summaryAlleleArray.summaryAlleleIds).toEqual(['sauid1', 'sauid2']);
  });

  it('should get total family variants count', () => {
    const summaryAlleleArray = new SummaryAllelesArray();
    const summaryAllele = new SummaryAllele();

    summaryAllele.numberOfFamilyVariants = 3;
    summaryAllele.sauid = 'sauid1';
    summaryAlleleArray.addSummaryAllele(summaryAllele);
    summaryAllele.numberOfFamilyVariants = 7;
    summaryAllele.sauid = 'sauid2';
    summaryAlleleArray.addSummaryAllele(summaryAllele);
    summaryAllele.numberOfFamilyVariants = 13;
    summaryAllele.sauid = 'sauid3';
    summaryAlleleArray.addSummaryAllele(summaryAllele);
    summaryAllele.numberOfFamilyVariants = 19;
    summaryAllele.sauid = 'sauid4';
    summaryAlleleArray.addSummaryAllele(summaryAllele);

    expect(summaryAlleleArray.totalFamilyVariantsCount).toEqual(76);
  });
});

describe('SummaryAllelesFilter', () => {
  it('should construct with default values', () => {
    const summaryAllelesFilter = new SummaryAllelesFilter();
    expect(summaryAllelesFilter.denovo).toBeTrue();
    expect(summaryAllelesFilter.transmitted).toBeTrue();
    expect(summaryAllelesFilter.codingOnly).toBeTrue();
    expect(summaryAllelesFilter.selectedAffectedStatus).toEqual(new Set());
    expect(summaryAllelesFilter.selectedEffectTypes).toEqual(new Set());
    expect(summaryAllelesFilter.selectedVariantTypes).toEqual(new Set());
  });

  it('should get min frequency', () => {
    const summaryAllelesFilter = new SummaryAllelesFilter();
    summaryAllelesFilter.selectedFrequencies = [-1, undefined];
    expect(summaryAllelesFilter.minFreq).toBe(null);
    summaryAllelesFilter.selectedFrequencies = [13, undefined];
    expect(summaryAllelesFilter.minFreq).toBe(13);
  });

  it('should get max frequency', () => {
    const summaryAllelesFilter = new SummaryAllelesFilter();
    summaryAllelesFilter.selectedFrequencies = [undefined, 17];
    expect(summaryAllelesFilter.maxFreq).toBe(17);
  });

  it('should filter summary variants array', () => {
    const summaryAllelesFilter = new SummaryAllelesFilter();
    const summaryAlleleArray = new SummaryAllelesArray();

    const row = {
      alleles: [
        // wanted allele
        {
          location: '1',
          is_denovo: false,
          seen_in_affected: true,
          seen_in_unaffected: false,
          variant: 'sub',
          effect: 'frame-shift',
          frequency: 10,
          position: 30,
          end_position: 30,
          family_variants_count: 1,
          chrom: '',
        },
        // wanted allele
        {
          location: '2',
          is_denovo: false,
          seen_in_affected: true,
          seen_in_unaffected: false,
          variant: 'CNV+',
          effect: 'CNV+',
          frequency: 5,
          position: 25,
          end_position: 35,
          family_variants_count: 1,
          chrom: '',
        },
        // unwanted allele
        {
          location: '3',
          // filtered out because:
          is_denovo: true,
          //
          seen_in_affected: true,
          seen_in_unaffected: false,
          variant: 'CNV+',
          effect: 'CNV+',
          frequency: 5,
          position: 25,
          end_position: 35,
          family_variants_count: 1,
          chrom: '',
        },
        // unwanted allele
        {
          location: '4',
          is_denovo: false,
          // filtered out because:
          seen_in_affected: false,
          seen_in_unaffected: true,
          //
          variant: 'sub',
          effect: 'CNV+',
          frequency: 5,
          position: 25,
          end_position: 35,
          family_variants_count: 1,
          chrom: '',
        },
        // unwanted allele
        {
          location: '5',
          is_denovo: false,
          seen_in_affected: true,
          seen_in_unaffected: false,
          // filtered out because:
          variant: 'fake',
          //
          effect: 'CNV+',
          frequency: 5,
          position: 25,
          end_position: 35,
          family_variants_count: 1,
          chrom: '',
        },
        // unwanted allele
        {
          location: '6',
          is_denovo: false,
          seen_in_affected: true,
          seen_in_unaffected: false,
          variant: 'sub',
          // filtered out because:
          effect: 'fake',
          //
          frequency: 5,
          position: 25,
          end_position: 35,
          family_variants_count: 1,
          chrom: '',
        },
        // unwanted allele
        {
          location: '7',
          is_denovo: false,
          seen_in_affected: true,
          seen_in_unaffected: false,
          variant: 'sub',
          effect: 'lgds',
          // filtered out because:
          frequency: 4,
          //
          position: 30,
          end_position: 30,
          family_variants_count: 1,
          chrom: '',
        },
        // unwanted allele
        {
          location: '8',
          is_denovo: false,
          seen_in_affected: true,
          seen_in_unaffected: false,
          variant: 'sub',
          effect: 'lgds',
          // filtered out because:
          frequency: 16,
          //
          position: 30,
          end_position: 30,
          family_variants_count: 1,
          chrom: '',
        },
        // unwanted allele
        {
          location: '9',
          is_denovo: false,
          seen_in_affected: true,
          seen_in_unaffected: false,
          variant: 'CNV+',
          effect: 'CNV+',
          frequency: 5,
          // filtered out because:
          position: 20,
          end_position: 24,
          //
          family_variants_count: 1,
          chrom: '',
        },
        // unwanted allele
        {
          location: '10',
          is_denovo: false,
          seen_in_affected: true,
          seen_in_unaffected: false,
          variant: 'CNV+',
          effect: 'CNV+',
          frequency: 5,
          // filtered out because:
          position: 36,
          end_position: 45,
          //
          family_variants_count: 1,
          chrom: '',
        },
        // unwanted allele
        {
          location: '11',
          is_denovo: false,
          seen_in_affected: true,
          seen_in_unaffected: false,
          variant: 'sub',
          effect: 'lgds',
          frequency: 10,
          // filtered out because:
          position: 24,
          end_position: 24,
          //
          family_variants_count: 1,
          chrom: '',
        },
      ]
    };
    summaryAlleleArray.addSummaryRow(row);

    summaryAllelesFilter.denovo = false;
    summaryAllelesFilter.selectedAffectedStatus = new Set(['Affected only']);
    summaryAllelesFilter.selectedEffectTypes = new Set([...LGDS, ...CODING, ...CNV]);
    summaryAllelesFilter.selectedVariantTypes = new Set(['sub', 'ins', 'del', 'CNV+', 'CNV-']);
    summaryAllelesFilter.selectedFrequencies = [5, 15];
    summaryAllelesFilter.selectedRegion = [25, 35];

    const filteredSummaryAllelesArray = summaryAllelesFilter.filterSummaryVariantsArray(summaryAlleleArray);

    expect(filteredSummaryAllelesArray.summaryAlleles).toEqual([
      summaryAlleleArray.summaryAlleles[0],
      summaryAlleleArray.summaryAlleles[1]
    ]);
  });

  it('should get query params', () => {
    const summaryAllelesFilter = new SummaryAllelesFilter();
    summaryAllelesFilter.codingOnly = false;
    summaryAllelesFilter.selectedAffectedStatus = new Set(['Affected only']);
    summaryAllelesFilter.selectedEffectTypes = new Set([...LGDS, ...CODING, ...CNV, ...OTHER]);
    summaryAllelesFilter.selectedVariantTypes = new Set(['sub', 'ins']);
    expect(summaryAllelesFilter.queryParams).toEqual({
      'effectTypes': [
        'frame-shift',
        'nonsense',
        'splice-site',
        'no-frame-shift-newStop',
        'missense',
        'no-frame-shift',
        'noStart',
        'noEnd',
        'synonymous',
        'CNV+',
        'CNV-',
        '3\'UTR',
        '3\'UTR-intron',
        '5\'UTR',
        '5\'UTR-intron',
        'intergenic',
        'intron',
        'non-coding',
        'non-coding-intron',
        'CDS',
      ],
      'inheritanceTypeFilter': ['denovo', 'mendelian', 'omission', 'missing'],
      'affectedStatus': ['Affected only'],
      'variantTypes': ['sub', 'ins']
    });
  });
});
