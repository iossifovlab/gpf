import { GetRegressionIdsPipe } from './get-regression-ids.pipe';

describe('ComparePipe', () => {
  it('should create an instance', () => {
    const pipe = new GetRegressionIdsPipe();
    expect(pipe).toBeTruthy();
  });

  it('should get regression ids', () => {
    const pipe = new GetRegressionIdsPipe();
    expect(pipe.transform('1,51')).toStrictEqual(['0', '1', '2', '3', 'length']);
    expect(pipe.transform({age: 'age at evaluation (in months)'})).toStrictEqual(['age']);
    expect(pipe.transform({age: ['1 year', '2 years'], first: ['second']})).toStrictEqual(['age', 'first']);
  });
});

