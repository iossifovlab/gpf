import { GetVariantReportRowsPipe } from './get-variant-report-rows.pipe';

describe('ComparePipe', () => {
  it('should create an instance', () => {
    const pipe = new GetVariantReportRowsPipe();
    expect(pipe).toBeTruthy();
  });

  it('should get variant reports rows', () => {
    const pipe = new GetVariantReportRowsPipe();
    expect(pipe.transform([
      'effectGroup1, effectGroup2, effectGroup3'], ['effectType1', 'effectType2', 'effectType3'
    ])).toStrictEqual(['effectGroup1, effectGroup2, effectGroup3', 'effectType1', 'effectType2', 'effectType3']);

    expect(pipe.transform([
      'effectGroup4, effectGroup5, effectGroup6'], ['effectType12', 'effectType26', 'effectType73'
    ])).not.toStrictEqual(['effectGroup5, effectGroup7, effectGroup8', 'effectType14', 'effectType12', 'effectType34']);

    expect(pipe.transform([
      'effectGroup11, effectGroup12, effectGroup13'], ['effectType14', 'effectType15', 'effectType16'
    ])).toStrictEqual(['effectGroup11, effectGroup12, effectGroup13', 'effectType14', 'effectType15', 'effectType16']);
  });
});
