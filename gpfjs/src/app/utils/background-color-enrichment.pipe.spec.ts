import { EnrichmentTestResult } from 'app/enrichment-query/enrichment-result';
import { BrowserQueryFilter, PersonSetCollection } from 'app/genotype-browser/genotype-browser';
import { BackgroundColorEnrichmentPipe } from './background-color-enrichment.pipe';
import { PValueIntensityPipe } from './p-value-intensity.pipe';

describe('BackgroundColorEnrichmentPipe', () => {
  it('should create an instance', () => {
    const pipe = new BackgroundColorEnrichmentPipe(new PValueIntensityPipe());
    expect(pipe).toBeTruthy();
  });

  it('should get rgba background color', () => {
    const pipe = new BackgroundColorEnrichmentPipe(new PValueIntensityPipe());
    expect(pipe.transform(new EnrichmentTestResult('name1', 2, 3, 4, 5,
      new BrowserQueryFilter(
        'name6', ['gene7', 'gene8'], ['effectType9', 'effectType10'],
        ['gender11', 'gender12'], new PersonSetCollection('id13', ['14', '15']),
        ['studyType16', 'studyType17'], ['variant18', 'variant19']
      ),
      new BrowserQueryFilter(
        'name20', ['gene21', 'gene22'], ['effectType23', 'effectType24'],
        ['gender25', 'gender26'], new PersonSetCollection('id27', ['28', '29']),
        ['studyType30', 'studyType31'], ['variant32', 'variant33']
      )))).toBe('rgba(255, 255, 255, 0.60)');
    expect(pipe.transform(new EnrichmentTestResult('name50', 49, 48, 47, 46,
      new BrowserQueryFilter(
        'name45', ['gene44', 'gene43'], ['effectType42', 'effectType41'],
        ['gender40', 'gender39'], new PersonSetCollection('id38', ['37', '36']),
        ['studyType35', 'studyType34'], ['variant33', 'variant32']
      ),
      new BrowserQueryFilter(
        'name31', ['gene30', 'gene29'], ['effectType28', 'effectType27'],
        ['gender26', 'gender25'], new PersonSetCollection('id24', ['23', '22']),
        ['studyType21', 'studyType20'], ['variant19', 'variant18']
      )))).toBe('rgba(255, 255, 255, 0.4)');
  });
});
