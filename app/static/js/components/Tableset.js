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
  
      let grid = [];
      grid.push(setkeys);

      this.cleanvalues.forEach(k => {
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
      return grid;
    }
    properCase(s) {
      return (!this.cleanvalues.has(s)) ? s : s.replace(/_/g, ' ').replace(/(?: |\b)(\w)/g, function(s) { return s.toUpperCase()});
    }

    copyToClipboard() {
      var r = document.createRange();
      r.selectNode(document.getElementById("itemDisplay"));
      window.getSelection().removeAllRanges(); 
      window.getSelection().addRange(r);
      document.execCommand('copy');
      window.getSelection().removeAllRanges();
    }

    renderView() {
        
        let grid = this.assembleKeys();
        let gridHTML = `<table class="grid">${grid.reduce((c, o) => c += `<tr id="${o[0]}">${o.reduce((c, d) => (c += `<td>${this.properCase(d)}</td>`), '')}</tr>`, '')}</table>`

    
        
        
        let pageContainerHTML = `
          <content>
            <div class="container">
              <div class="tables">
                <div id="itemDisplay">
                  ${gridHTML}
                </div>
              </div>
            </div>
          </content>
        `;
        return pageContainerHTML;
      }
    };
    
