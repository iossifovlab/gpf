import { UndirectedGraph, Graph, getOtherVertex, equalEdges, Edge, Vertex } from '../utils/undirected-graph';

import { equal } from '../utils/sets-helper';

export class Interval {
  public constructor(
    public left = 0,
    public right = 1
  ) {}
}

export class IntervalForVertex<T> extends Interval {
  public constructor(
    public vertex: Vertex<T>,
    left = 0,
    right = 1
  ) {
    super(left, right);
  }

  public copy(): IntervalForVertex<T> {
    return new IntervalForVertex<T>(
      this.vertex,
      this.left,
      this.right
    );
  }

  public toString(): string {
    return `i[${this.vertex}> ${this.left}:${this.right}]`;
  }
}

export class Realization<T> {
  public constructor(
    public graph: Graph<T>,
    public forbiddenGraph: Graph<T>,
    public intervals: Array<IntervalForVertex<T>> = new Array<IntervalForVertex<T>>(),
    public domain: Array<Vertex<T>> = new Array<Vertex<T>>(),
    public maxWidth = 3,
  ) {}

  public toString(): string {
    const orderedDomain = this.domain.map(v => v.toString()).sort((a, b) => a.localeCompare(b));
    return orderedDomain.join(';');
  }

  public clone(): Realization<T> {
    return new Realization(
      this.graph,
      this.forbiddenGraph,
      this.intervals.map(i => i.copy()),
      this.domain.slice(0)
    );
  }

  public extend(vertex: Vertex<T>): boolean {
    if (!this.canExtend(vertex)) {
      return false;
    }

    const maxRight = Math.max(...Array.from(this.maximalSet()).map(v => this.getInterval(v).right));
    const p = 0.5 + maxRight;

    for (const activeVertex of this.getActiveVertices()) {
      const activeInterval = this.getInterval(activeVertex);
      activeInterval.right = p + 1;
    }

    const newInterval = new IntervalForVertex(vertex, p, p + 1);
    this.domain.push(vertex);
    this.intervals.push(newInterval);

    // maybe add edge to graph?

    return true;
  }

  public canExtend(newVertex: Vertex<T>): boolean {
    const tempRealization = new Realization(
      this.graph,
      this.forbiddenGraph,
      this.intervals.concat([new IntervalForVertex(newVertex)]), // dummy interval
      this.domain.concat([newVertex]));

    const newActiveVertices = tempRealization.getActiveVertices();
    if (newActiveVertices.length >= tempRealization.maxWidth) {
      return false;
    }

    // console.log("Checking forbidden");
    const thisActiveVertices = this.getActiveVertices();
    const forbiddenEdges = this.forbiddenGraph.getEdgesForVertex(newVertex);
    for (const activeVertex of thisActiveVertices) {
      if (forbiddenEdges.some(edge => getOtherVertex(newVertex, edge) === activeVertex)) {
        return false;
      }
    }

    // console.log("Checking expected dangling");
    for (const activeVertex of this.getActiveVertices()) {
      const thisDangling = this.dangling(activeVertex);
      const otherDangling = tempRealization.dangling(activeVertex);
      const newEdge: Edge<T> = [activeVertex, newVertex];

      for (const thisEdge of thisDangling) {
        const expectedNewDangling = otherDangling.concat([newEdge]);
        if (!expectedNewDangling.some(edge => equalEdges(edge, thisEdge))) {
          return false;
        }
      }
    }

    // console.log("Checking new vertex dangling");
    const newDangling = tempRealization.dangling(newVertex);
    const newVertexEdges = this.graph.getEdgesForVertex(newVertex);
    for (const danglingEdge of newDangling) {
      if (!newVertexEdges.some(
        edge => equalEdges(edge, danglingEdge) || (this.domain.indexOf(getOtherVertex(newVertex, edge)) === -1))
      ) {
        return false;
      }
    }

    // console.log("Checking active");
    const activeVerticesNonEmptyDanglingAndNew = thisActiveVertices.filter(
      v => tempRealization.dangling(v).length !== 0
    ).concat([newVertex]);
    for (const newActiveVertex of newActiveVertices) {
      if (activeVerticesNonEmptyDanglingAndNew.indexOf(newActiveVertex) === -1) {
        return false;
      }
    }

    // console.log("Can extend :)");
    return true;
  }

  public isEquivalent(other: Realization<T>): boolean {
    if (!equal(new Set(this.domain), new Set(other.domain))) {
      return false;
    }
    if (!equal(new Set(this.getActiveVertices()), new Set(other.getActiveVertices()))) {
      return false;
    }

    for (const activeVertex of Array.from(this.getActiveVertices())) {
      if (!equal(new Set(this.dangling(activeVertex)), new Set(other.dangling(activeVertex)))) {
        return false;
      }
    }
    return true;
  }

  public getActiveVertexEdges(vertex: Vertex<T>): Edge<T>[] {
    return this.graph.getEdgesForVertex(vertex).filter(edge => {
      const otherVertex = edge[1];
      return this.domain.indexOf(otherVertex) === -1;
    });
  }

  public getActiveVertexEdge(vertex: Vertex<T>): Edge<T> {
    return this.graph.getEdgesForVertex(vertex).find(edge => {
      const otherVertex = edge[1];
      return otherVertex && this.domain.indexOf(otherVertex) === -1;
    });
  }

  public isActiveVertex(vertex: Vertex<T>): boolean {
    return Boolean(this.getActiveVertexEdge(vertex));
  }

  public getActiveVertices(): T[] {
    const result = new Array<Vertex<T>>();
    for (const vertex of this.domain) {
      if (this.isActiveVertex(vertex) && result.indexOf(vertex) === -1) {
        result.push(vertex);
      }
    }
    return result;
  }

  public dangling(vertex: Vertex<T>): Edge<T>[] {
    return this.getActiveVertexEdges(vertex);
  }

  public maximalSet(): Set<T> {
    const result = new Set<Vertex<T>>();

    for (const vertex of this.domain) {
      if (this.isMaximal(vertex)) {
        result.add(vertex);
      }
    }

    return result;
  }

  public isMaximal(vertex: Vertex<T>): boolean {
    for (const domainVertex of this.domain) {
      if (domainVertex !== vertex && this.isInIntervalOrder(vertex, domainVertex)) {
        return false;
      }
    }
    return true;
  }

  public isLayout(): boolean {
    if (this.domain.length === 0) {
      return false;
    }

    const activeVertices = this.getActiveVertices();
    for (const vertex of activeVertices) {
      if (!this.isMaximal(vertex)) {
        return false;
      }
    }

    return true;
  }

  public isMaximum(vertex: Vertex<T>): boolean {
    const interval = this.getInterval(vertex);
    if (!interval) {
      return false;
    }


    for (const domainInterval of this.intervals) {
      if (interval.left < domainInterval.left) {
        return false;
      }
    }

    return true;
  }

  public isInIntervalOrder(a: Vertex<T>, b: Vertex<T>): boolean {
    const intervalA = this.getInterval(a);
    const intervalB = this.getInterval(b);

    if (intervalA === null || intervalB === null) {
      return false;
    }

    return intervalA.right < intervalB.left;
  }

  private getInterval(vertex: T): IntervalForVertex<T> {
    const index = this.domain.indexOf(vertex);
    if (index === -1) {
      return null;
    }
    return this.intervals[index];
  }
}

export class SandwichInstance<T> {
  public constructor(
    public vertices: Array<Vertex<T>>,
    public required: Set<Edge<T>>,
    public forbidden: Set<Edge<T>>
  ) {}
}

export function solveSandwich<T>(sandwichInstance: SandwichInstance<T>): IntervalForVertex<T>[] {
  const requiredGraph = new UndirectedGraph<T>();
  const forbiddenGraph = new UndirectedGraph<T>();

  for (let vertex of sandwichInstance.vertices) {
    requiredGraph.addVertex(vertex);
    forbiddenGraph.addVertex(vertex);
  }

  for (let edge of Array.from(sandwichInstance.required)) {
    requiredGraph.addEdge(edge[0], edge[1]);
  }

  for (let edge of Array.from(sandwichInstance.forbidden)) {
    forbiddenGraph.addEdge(edge[0], edge[1]);
  }

  let start = Date.now();
  let lexicalSort = (a: {}, b: {}) => a.toString().localeCompare(b.toString());

  let realizationsQueue = new Array<Realization<T>>();

  for (let vertex of sandwichInstance.vertices) {
    realizationsQueue.push(
      new Realization(requiredGraph, forbiddenGraph,
                      [new IntervalForVertex(vertex)], [vertex])
    );
  }
  realizationsQueue = realizationsQueue.sort(lexicalSort);

  let visitedRealizationMap = {};
  let currentIteration = 0;

  while (realizationsQueue.length !== 0) {
    let currentRealization = realizationsQueue.pop();

    let leftVertices = sandwichInstance.vertices
      .filter(vertex => currentRealization.domain.indexOf(vertex) === -1);
    if (leftVertices.length === 0) {
      return currentRealization.intervals;
    }
    leftVertices = leftVertices.sort(lexicalSort);

    if (currentIteration === 1000) {
      console.warn('Premature termination on', currentIteration, 'iterations');
      return null;
    }


    for (let vertex of leftVertices) {
      let currentRealizationCopy = currentRealization.clone();
      let successfulExtension = currentRealizationCopy.extend(vertex);
      // console.log("Success?", successfulExtension);

      if (!successfulExtension) {
        continue;
      }

      if (sandwichInstance.vertices.length === currentRealizationCopy.domain.length) {
        // console.log("Took", Date.now() - start, "ms");
        // console.log(currentRealizationCopy.intervals.map(i => i.toString()))
        return currentRealizationCopy.intervals;
      } else {
        // console.log("Checking realization", currentRealizationCopy);
        let realizationString = currentRealizationCopy.toString();
        if (!visitedRealizationMap[realizationString]) {
          realizationsQueue.push(currentRealizationCopy);
          visitedRealizationMap[realizationString] = true;
        }
      }
    }
  }

  return null;
}
