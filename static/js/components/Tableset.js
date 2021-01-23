/*
 * Manages positioning, navigation through items
 * Could build this out to expand with repeated service requests using offset
 */
class Tableset {
    constructor(datasetArray) {
      this._datasets = datasetArray;
    }
  
    get datasets() {
      return this._datasets;
    }
    set datasets(datasets) {
      this._datasets = datasets;
    }

  
    assembleKeys() {
      let setkeys = ['Measure']; //Object.keys(this.datasets);
      let setvalues = [];
      
      Object.entries(this.datasets).forEach(([key, value]) => {
        setkeys.push(key);
        Object.entries(value).forEach(( [ikey, value]) => setvalues.push(ikey));
      })
      let cleanvalues = new Set(setvalues)
      //console.log(setkeys)
      //console.log(cleanvalues)

      let grid = [];
      grid.push(setkeys);
      //console.log(grid);
      //setkeys.shift();

      cleanvalues.forEach(k => {
        //console.log(k);
        let row = [];
        row.push(k);
        setkeys.forEach(sys => {
          if (sys == 'Measure') return;
          if (this.datasets[sys] === undefined )  {row.push('-'); return}  
          if (this.datasets[sys][k] === undefined ) {row.push('-'); return}
          row.push((this.datasets[sys][k]) )      
        })
        grid.push(row)
      });
      console.log(grid);
      return grid;
    }

    toDiv() {
        let grid = this.assembleKeys();
        let gridHTML = `<table class="grid">${grid.reduce((c, o) => c += `<tr>${o.reduce((c, d) => (c += `<td>${d}</td>`), '')}</tr>`, '')}</table>`

        let tablesHTML = "";
        let counter = 1;
        Object.entries(this.datasets).forEach(([key, value]) => {
          tablesHTML+=`<table class="tableSet" id="${key}">`
          Object.entries(value).forEach(([ikey, value]) => tablesHTML+=(`<tr><td>${key}</td><td>${ikey}</td><td>${value}</td></tr>`));
          tablesHTML+='</table>'
        })
        let pageContainerHTML = `
          <content>
          <div class="container">
            <div class="tables">
            <div id="itemDisplay">
               ${gridHTML}
             
               
      
            </div>
          </div>
        </content>
        `;
        return pageContainerHTML;
      }
    };
    
