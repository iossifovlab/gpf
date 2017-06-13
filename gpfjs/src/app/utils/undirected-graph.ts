export class UndirectedGraph<T> {

  private vertices: Array<T> = new Array<T>();
  private edges: Array<Array<[T, T]>>;

  addVertex(vertex: T, edges: Array<[T, T]> = []) {
    this.checkCorrectEdges(vertex, edges);

    this.vertices.push(vertex);
    this.edges.push(edges);

    for (let edge of edges) {
      let otherVertex = this.getOtherVertex(vertex, edge);
      this.getEdgesForVertex(otherVertex).push(edge);
    }
  }

  addEdge(vertex1: T, vertex2: T) {
    this.checkVertex(vertex1);
    this.checkVertex(vertex2);

    let edge: [T, T] = [vertex1, vertex2];

    this.getEdgesForVertex(vertex1).push(edge);
    this.getEdgesForVertex(vertex2).push(edge);

  }

  getEdgesForVertex(vertex: T) {
    let index = this.vertices.indexOf(vertex);

    if (index === -1) {
      return [];
    }

    return this.edges[index];
  }

  hasVertex(vertex: T) {
    return this.vertices.indexOf(vertex) !== -1;
  }

  hasEdge(vertex1: T, vertex2: T) {
    if (!this.hasVertex(vertex1) || !this.hasVertex(vertex2)) {
      return false;
    }

    for (let edge of this.getEdgesForVertex(vertex1)) {
      if (edge[0] === vertex2 || edge[1] === vertex2) {
        return true;
      }
    }

    return false;
  }

  getVertices() {
    return this.vertices;
  }

  getEdges() {
    let allEdges: [T, T][] = [];
    let alreadyAddedVertices: T[] = [];

    for (let i = 0; i < this.edges.length; i++) {
      let it = this.edges[i].entries();
      let res = it.next();

      while (!res.done) {
        let [, edge] = res.value;
        if (alreadyAddedVertices.indexOf(edge[0]) === -1 &&
            alreadyAddedVertices.indexOf(edge[1]) === -1) {
          allEdges.push(edge);
        }

        res = it.next();
      }
      alreadyAddedVertices.push(this.vertices[i]);
    }

    return allEdges;
  }

  private checkCorrectEdges(vertex: T, edges: Array<[T, T]>) {
    for (let edge of edges) {
      let otherVertex: T = this.getOtherVertex(vertex, edge);

      if (otherVertex == null) {
        throw `Edge (${edge[0]}, ${edge[1]}) does not have vertex ${vertex}`;
      }

      this.checkVertex(otherVertex);
    }
  }

  private checkVertex(vertex: T) {
    if (!this.hasVertex(vertex)) {
      throw `Graph does not have vertex ${vertex}`;
    }
  }

  private getOtherVertex(vertex: T, edge: [T, T]) {
    let otherVertex: T = null;

    if (edge[0] === vertex) {
      otherVertex = edge[1];
    } else if (edge[1] === vertex) {
      otherVertex = edge[0];
    }

    return otherVertex;
  }
}
