import { Component, EventEmitter, Input, OnChanges, OnInit, Output, ViewChild } from '@angular/core';
import { DatasetNode } from 'app/dataset-node/dataset-node';
@Component({
  selector: 'gpf-treelist-checkbox',
  templateUrl: './treelist-checkbox.component.html',
  styleUrls: ['./treelist-checkbox.component.css']
})
export class StudyFiltersTreeComponent implements OnInit, OnChanges {
  @Output() public checkboxChangeEvent = new EventEmitter<string>();

  @Input()
  public data: DatasetNode;

  @Input()
  public selectedStudies: Set<string>;

  @ViewChild('hide') public input;

  public ngOnInit(): void {
    this.selectedStudies?.clear();
    this.updateFilterStates(this.data);
  }

  public ngOnChanges(): void {
    this.updateFilterStates(this.data);
  }

  /* eslint-disable */
  public updateFilters($event): void {
    const datasetNode = findNodeById(this.data, $event.target.getAttribute('id'));
    if ($event.target.checked) {
      if (datasetNode.children.length > 0) {
        this.getAllChildren(datasetNode.children).forEach(child => {
          this.selectedStudies.add(child);
        });
      } else {
        this.selectedStudies.add(datasetNode.dataset.id);
      }
    } else {
      if (datasetNode.children.length > 0) {
        this.getAllChildren(datasetNode.children).forEach(child => {
          this.selectedStudies.delete(child);
        });
      }
      this.selectedStudies.delete($event.target.id);
    }
    this.checkboxChangeEvent.emit($event.target.id);
    this.updateFilterStates(this.data);
  }
  /* eslint-enable */

  private setCheckbox(checkboxName: string, flag: number): void {
    const elements = document.querySelectorAll(`[id='${checkboxName}']`);
    elements.forEach(element => {
      (element as HTMLInputElement).checked = flag !== 0;
      (element as HTMLInputElement).indeterminate = flag === 1;
    });
  }

  public updateFilterStates(data: DatasetNode): void {
    let checkState = 0;
    data.children.forEach(child => {
      if (child.children.length > 0) {
        this.updateFilterStates(child);
      }
    });
    const children = this.getAllChildren(data.children);
    let selectedCount = 0;
    children.forEach(child => {
      if (this.selectedStudies.has(child)) {
        selectedCount += 1;
      }
    });
    if (selectedCount === children.size) {
      checkState = 2;
    } else if (selectedCount > 0) {
      checkState = 1;
    }
    this.setCheckbox(data.dataset.id, checkState);
  }

  public getAllChildren(
    container: DatasetNode[], list: Set<string> = null, includeDatasets: boolean = false
  ): Set<string> {
    if (list === null) {
      list = new Set<string>();
    }

    container.forEach(child => {
      if (child.children.length === 0 || includeDatasets) {
        list = list.add(child.dataset.id);
      }
      if (child.children.length > 0) {
        list = this.getAllChildren(child.children, list);
      }
    });
    return list;
  }
}

// eslint-disable-next-line prefer-arrow/prefer-arrow-functions
export function findNodeById(node: DatasetNode, id: string): DatasetNode | undefined {
  if (node.dataset.id === id) {
    return node;
  }

  if (node.children) {
    for (const child of node.children) {
      const foundNode = findNodeById(child, id);
      if (foundNode) {
        return foundNode;
      }
    }
  }
  return undefined;
}
