import { GpfjsPage } from './app.po';

describe('gpfjs App', function() {
  let page: GpfjsPage;

  beforeEach(() => {
    page = new GpfjsPage();
  });

  it('should display message saying app works', () => {
    page.navigateTo();
    expect(page.getParagraphText()).toEqual('app works!');
  });
});
