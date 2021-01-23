/*
 * Manages positioning, navigation through items
 * Could build this out to expand with repeated service requests using offset
 */
class Tableset {
    constructor(datasetArray) {
      this._datasets = datasetArray;
      this._cleanvalues = undefined;
    }
  
    get datasets() {
      return this._datasets;
    }
    set datasets(datasets) {
      this._datasets = datasets;
    }
    
    get cleanvalues() {
      return this._cleanvalues;
    }

    set cleanvalues(cleanvalues) {
      this._cleanvalues = cleanvalues;
    }
    
    assembleKeys() {
      let setkeys = ['Measure']; //Object.keys(this.datasets);
      let setvalues = [];
      
      Object.entries(this.datasets).forEach(([key, value]) => {
        setkeys.push(key);
        Object.entries(value).forEach(( [ikey, value]) => setvalues.push(ikey));
      })
      this.cleanvalues = new Set(setvalues)
      //console.log(setkeys)
      //console.log(cleanvalues)

      let grid = [];
      grid.push(setkeys);
      //console.log(grid);
      //setkeys.shift();
      
      this.cleanvalues.forEach(k => {
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
      //console.log(grid);
      return grid;
    }
    properCase(s) {
      return (!this.cleanvalues.has(s)) ? s : s.replace(/_/g, ' ').replace(/(?: |\b)(\w)/g, function(s) { return s.toUpperCase()});
    }
    toDiv() {
        
        let grid = this.assembleKeys();
        let gridHTML = `<table class="grid">${grid.reduce((c, o) => c += `<tr id="${o[0]}">${o.reduce((c, d) => (c += `<td>${this.properCase(d)}</td>`), '')}</tr>`, '')}</table>`

        /*
        let tablesHTML = "";
        let counter = 1;
        Object.entries(this.datasets).forEach(([key, value]) => {
          tablesHTML+=`<table class="tableSet" id="${key}">`
          Object.entries(value).forEach(([ikey, value]) => tablesHTML+=(`<tr><td>${key}</td><td>${ikey}</td><td>${value}</td></tr>`));
          tablesHTML+='</table>'
        })
        */
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
    
