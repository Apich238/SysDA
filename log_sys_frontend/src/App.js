import React,{useState} from 'react';
import Tree from 'react-d3-tree';
import axios from 'axios';

function App() {
  const [formula,setformula]=useState( "~(a>0.1)&(b>=0.3)")
  const [tree,set_tree]=useState( {name:'root'})
  async function get_tree(e){
    const resp = await axios.post('http://localhost:8001/make_tree',
                     {formula: formula})
    set_tree(resp.data)
  }

  return (
    <div className="App">
      <input
        type="text"
        value={formula}
        onChange = {event=> setformula(event.target.value)}
        style={{width:'40em'}}
      />
      <button onClick={get_tree}>построить дерево</button>
      <div style={{ width: '50em', height: '40em' }}>
        <Tree
          data={tree}
          pathFunc="step"
          orientation='vertical'
          nodeSize= {{x:120,y:40}}
          translate={{ x: 300, y: 30 }}
        />
      </div>
    </div>
  );
}

export default App;
