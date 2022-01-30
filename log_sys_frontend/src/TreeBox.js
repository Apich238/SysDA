import React, {useState} from 'react';

class TreeBox extends React.Component {


    constructor({tree, ...props}) {
      super(props);
      this.state={
        treeF: tree
      }
      this.setTree=this.setTree.bind(this);
    }

    setTree (newtree){
      this.setState({treeF : newtree});
    }
    render() {
      return (
        <div
          className = "tree_view">
            <p>тут будет отрисовка дерева</p>
            {this.state.treeF}
        </div>
      )
    }
}

export default TreeBox;