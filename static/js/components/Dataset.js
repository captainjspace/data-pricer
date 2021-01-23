/*
 * Manages display of pricing data
 * 
 */
class Dataset {

    constructor(inputs,data,globals) {
      this._inputs = inputs;
      this._data = data; ;
      this._globals = globals;
    }
  
    get inputs() {
      return this._inputs;
    }
    set inputs(inputs) {
      this._inputs = inputs;
    }
    get data() {
      return this._data;
    }
    set data(data) {
      this._data = data;
    }
    get globals() {
      return this._globals;
    }
    set globals(globals) {
        this._globals = globals;
    };

    /*
     * build table the pager body html
     * optimize further by making smaller objects
     * (i.e., avoid click event re-attachment)
     */
    toDiv(counter) {
    
      let datasetHTML = `
        <content>
          <div class="dataset">

            <div class="data-table" id="${counter}">
              ${this._data} 
            </div>

          </div>
      </content>
      `;
      return datasetHTML;
    }
  
  }