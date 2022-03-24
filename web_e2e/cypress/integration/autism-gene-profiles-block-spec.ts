import { AutismGeneProfilesBlock } from 'cypress/elements/autism-gene-profiles-block-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';
import { sidenavPageLinks } from 'cypress/elements/utils';

describe('Autism gene profiles block tests', () => {
  const page = new AutismGeneProfilesBlock();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should display autism gene profiles table', () => {
    autismGeneProfilesTablePage.window.should('be.visible');
  });

  it('should display the keybind icon', () => {
    page.keybindIcon.should('be.visible');
  });

  it('should mouseover the keybind icon to show the keybind tool tip and then mouseout to hide it', () => {
    page.keybindTooltip.should('not.exist');

    page.keybindIcon.trigger('mouseover');
    page.keybindTooltip.should('be.visible');

    page.keybindIcon.trigger('mouseout');
    page.keybindTooltip.should('not.exist');
  });
});
