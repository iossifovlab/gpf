import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, map, Observable } from 'rxjs';
import { ConfigService } from '../config/config.service';
import { DatasetNode } from 'app/dataset-node/dataset-node';
import { DatasetHierarchy } from './datasets';

@Injectable()
export class DatasetsTreeService {
  private readonly datasetHierarchyUrl = 'datasets/hierarchy';
  private datasetTreeNodes$: BehaviorSubject<object> = new BehaviorSubject<object>(null);

  public constructor(
    private http: HttpClient,
    private config: ConfigService
  ) {
    const options = { withCredentials: true };
    this.http.get(`${this.config.baseUrl}${this.datasetHierarchyUrl}`, options).subscribe(
      data => {
        this.datasetTreeNodes$.next(data);
      }
    );
  }

  // This method finds Dataset Node by its id
  public findNodeById(node: DatasetNode, id: string): DatasetNode | undefined {
    if (node.dataset.id === id) {
      return node;
    }
    if (node.children) {
      for (const child of node.children) {
        const foundNode = this.findNodeById(child, id);
        if (foundNode) {
          return foundNode;
        }
      }
    }
    return undefined;
  }

  // This method works with the backend derived treelist data structure and finds it by id
  public findHierarchyNode(node: object, id: string): object {
    if (node['dataset'] === id) {
      return node;
    }
    if (node['children']) {
      for (const child of node['children']) {
        const foundNode = this.findHierarchyNode(child as object, id);
        if (foundNode) {
          return foundNode;
        }
      }
    }
    return undefined;
  }

  public async getUniqueLeafNodes(dataset: string): Promise<Set<string>> {
    const uniqueLeafNodes = new Set<string>();
    const subject = new Set<string>();
    await new Promise<void>(resolve => {
      this.datasetTreeNodes$.subscribe(datasetTreeNodes => {
        if (datasetTreeNodes) {
          for (const node of datasetTreeNodes['data']) {
            const matchingNode = this.findHierarchyNode(node as object, dataset);
            if (matchingNode) {
              this.addAllLeafNodes(matchingNode, uniqueLeafNodes);
            }
          }
          uniqueLeafNodes.forEach(node => subject.add(node));
          resolve();
        }
      });
    });
    return subject;
  }

  private addAllLeafNodes(node: object, leafNodes: Set<string>): void {
    if (!node) {
      return;
    }

    if (node['children'] && (node['children'] as ArrayLike<object>).length > 0) {
      for (const child of node['children']) {
        this.addAllLeafNodes(child as object, leafNodes);
      }
    } else {
      leafNodes.add(node['dataset'] as string);
    }
  }

  public getDatasetHierarchy(): Observable<DatasetHierarchy[]> {
    const options = { withCredentials: true };
    return this.http.get(`${this.config.baseUrl}${this.datasetHierarchyUrl}`, options).pipe(
      map((json: {data: object[]}) => json.data.map(d => DatasetHierarchy.fromJson(d)))
    );
  }
}
