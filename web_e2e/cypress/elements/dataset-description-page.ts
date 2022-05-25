import { BasePage } from './utils';

export class DatasetDescriptionPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-dataset-description');
  }

  public get emptyDescriptionPlaceholder(): element {
    return cy.get('#empty-description');
  }

  public get descriptionText(): element {
    return cy.get('markdown p');
  }

  public get editIcon(): element {
    return cy.get('#edit-icon');
  }

  public get editorWindow(): element {
    return cy.get('.editor');
  }

  public get editorHeader(): element {
    return cy.get('.md-header');
  }

  public get editorPrevieButton(): element {
    return cy.get('button').contains('Preview');
  }

  public get editorSaveButton(): element {
    return cy.get('button').contains('Save');
  }

  public get editorCloseButton(): element {
    return cy.get('button').contains('Close');
  }

  public get editorTextarea(): element {
    return this.editorWindow.find('textarea');
  }

  public clearDescription(): void {
    this.editIcon.click();
    this.editorTextarea.clear();
    this.editorSaveButton.click();
    this.emptyDescriptionPlaceholder.should('be.visible');
  }
}
