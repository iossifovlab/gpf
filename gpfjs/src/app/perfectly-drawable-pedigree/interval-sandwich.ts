import { Vertex, Edge } from './perfectly-drawable-pedigree.component';
import { UndirectedGraph, Graph, getOtherVertex,
  equalEdges } from '../utils/undirected-graph';

import { hasIntersection, intersection, equal,
  isSubset } from '../utils/sets-helper';

export class Interval {
  constructor(
    public left = 1,
    public right = 1
  ) {}
}

export class Realization {
  constructor(
    public graph: Graph<Vertex>,
    public forbiddenGraph: Graph<Vertex>,
    public intervals: Array<Interval> = new Array<Interval>(),
    public domain: Array<Vertex> = new Array<Vertex>(),
  ) {}

  extend(vertex: Vertex) {
    if (!this.canExtend(vertex)) {
      return false;
    }

    let maxRight = Math.max(...Array.from(this.maximalSet())
      .map(v => this.getInterval(v).right));

    let p = 0.5 + maxRight;

    for (let activeVertex of Array.from(this.getActiveVertices())) {
      let activeInterval = this.getInterval(activeVertex);
      activeInterval.right = p + 1;
    }

    let newInterval = new Interval(p, p + 1);
    this.domain.push(vertex);
    this.intervals.push(newInterval);

    // maybe add edge to graph?

    return true;
  }

  canExtend(newVertex: Vertex) {
    let tempRealization = new Realization(
      this.graph,
      this.forbiddenGraph,
      this.intervals.concat([new Interval()]), // dummy interval
      this.domain.concat([newVertex]));


    for (let activeVertex of Array.from(this.getActiveVertices())) {
      let thisDangling = this.dangling(activeVertex);
      let otherDangling = tempRealization.dangling(activeVertex);
      let newEdge: [Vertex, Vertex] = [activeVertex, newVertex];

      for (let thisEdge of Array.from(thisDangling)) {
        let expectedNewDangling = Array.from(otherDangling).concat([newEdge]);
        if (!expectedNewDangling.some(edge => equalEdges(edge, thisEdge))) {
          return false;
        }
      }
    }


    let newDangling = tempRealization.dangling(newVertex);
    let newVertexEdges = this.graph.getEdgesForVertex(newVertex);
    for (let danglingEdge of Array.from(newDangling)) {
      if (newVertexEdges.some(
          edge => equalEdges(edge, danglingEdge) ||
                  (this.domain.indexOf(getOtherVertex(newVertex, edge)) === -1))
          ) {
        return false;
      }
    }


    let newActiveVertices = tempRealization.getActiveVertices();
    let thisActiveVertices = Array.from(this.getActiveVertices());
    let activeVerticesNonEmptyDanglingAndNew =
      thisActiveVertices.filter(v => tempRealization.dangling(v).size !== 0)
      .concat([newVertex]);
    for (let newActiveVertex of Array.from(newActiveVertices)) {
      if (activeVerticesNonEmptyDanglingAndNew.indexOf(newActiveVertex) === -1) {
        return false;
      }
    }


    let forbiddenEdges = this.forbiddenGraph.getEdgesForVertex(newVertex);
    for (let activeVertex of thisActiveVertices) {
      if (forbiddenEdges.some(edge => getOtherVertex(newVertex, edge) === activeVertex)) {
        return false;
      }
    }
  }

  isEquivalent(other: Realization) {
    if (!equal(new Set(this.domain), new Set(other.domain))) {
      return false;
    }
    if (!equal(this.getActiveVertices(), other.getActiveVertices())) {
      return false;
    }

    for (let activeVertex of Array.from(this.getActiveVertices())) {
      if (!equal(this.dangling(activeVertex), other.dangling(activeVertex))) {
        return false;
      }
    }

    return true;
  }

  getActiveVertexEdge(vertex: Vertex) {
    return this.graph.getEdgesForVertex(vertex).find(edge => {
      let otherVertex = getOtherVertex(vertex, edge);
      return otherVertex && this.domain.indexOf(otherVertex) === -1;
    });
  }

  isActiveVertex(vertex: Vertex) {
    return !!this.getActiveVertexEdge(vertex);
  }

  getActiveVertices() {
    let result = new Set<Vertex>();
    for (let vertex of this.domain) {

      if (this.isActiveVertex(vertex)) {
        result.add(vertex);
      }
    }

    return result;
  }

  dangling(vertex: Vertex) {
    if (!this.isActiveVertex(vertex)) {
      return new Set<Edge>();
    }

    let edgesArray = this.graph.getEdgesForVertex(vertex).filter(edge => {
      let otherVertex = getOtherVertex(vertex, edge);
      return this.domain.indexOf(otherVertex) === -1;
    });

    return new Set<Edge>(edgesArray);
  }

  maximalSet() {
    let result = new Set<Vertex>();

    for (let vertex of this.domain) {
      if (this.isMaximal(vertex)) {
        result.add(vertex);
      }
    }

    return result;
  }

  isMaximal(vertex: Vertex) {
    for (let domainVertex of this.domain) {
      if (domainVertex !== vertex && this.isInIntervalOrder(vertex, domainVertex)) {
        return false;
      }
    }
    return true;
  }

  isLayout() {
    if (this.domain.length === 0) {
      return false;
    }

    let activeVertices = this.getActiveVertices();
    for (let vertex of Array.from(activeVertices)) {
      if (!this.isMaximal(vertex)) {
        return false;
      }
    }

    return true;
  }

  isMaximum(vertex: Vertex) {
    let interval = this.getInterval(vertex);
    if (!interval) {
      return false;
    }


    for (let domainInterval of this.intervals) {
      if (interval.left < domainInterval.left) {
        return false;
      }
    }

    return true;
  }

  isInIntervalOrder(a: Vertex, b: Vertex) {
    let intervalA = this.getInterval(a);
    let intervalB = this.getInterval(b);

    if (intervalA === null || intervalB === null) {
      return false;
    }

    return intervalA.right < intervalB.left;
  }

  private getInterval(vertex: Vertex) {
    let index = this.domain.indexOf(vertex);
    if (index === -1) {
      return null;
    }
    return this.intervals[index];
  }
}

export class SandwichInstance {
  constructor(
    public vertices: Array<Vertex>,
    public required: Set<Edge>,
    public forbidden: Set<Edge>
  ) {}
}

export function solveSandwich(sandwichInstance: SandwichInstance) {
  let requiredGraph = new UndirectedGraph<Vertex>();
  let forbiddenGraph = new UndirectedGraph<Vertex>();

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

  return true;

  // for(let vertex in sandwichInstance.vertices) {
  //
  // }
}
