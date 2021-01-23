'use strict';
/* seed search */
const seedSearch = 'destiny';

/*
 * this is the constant header and first child Node of the body - note the video player
 * could add all this via js, but I demonstrate that below in init function
 */
const mastHTML = `
    <img id="gclogo" src="/static/img/cloud-logo.svg"> 
    <div class="flex-columns">
      <div id="inputBox">
        <div class="form-field">
          <div class="form-field__control">
            <input type="text" id="reads" class="form-field__input" placeholder=" "  autofocus />
            <label for="reads" class="form-field__label">Reads per Second</label>
            <div class="form-field__bar"></div>
          </div>
        </div>
        <div class="form-field">
          <div class="form-field__control">
            <input type="text" id="writes" class="form-field__input" placeholder=" "   />
            <label for="writes" class="form-field__label">Writes per Second</label>
            <div class="form-field__bar"></div>
          </div>
        </div>
        <div class="form-field">
          <div class="form-field__control">
            <input type="text" id="storage" class="form-field__input" placeholder=" "  />
            <label for="storage" class="form-field__label">Storage (TB)</label>
            <div class="form-field__bar"></div>
          </div>
        </div>
        <div class="form-field">
          <div class="form-field__control">
            <input type="text" id="scale" class="form-field__input" placeholder=" "  />
            <label for="scale" class="form-field__label">Growth Scale (0.0-1.0)</label>
            <div class="form-field__bar"></div>
          </div>
        </div>
  
        <input type="button" value="Get Estimates"
               onClick="app.getEstimates()")>
      </div>
      <div id="dataport">
      </div>
    </div>
`;

/*
 * @filename App.js
 * Main application facade, wraps core functions, view controller
 */
class Inputs {

    constructor() {
        this._reads = 30000;
        this._writes = 20000;
        this._storage = 100
        this._scale = 0.1;  
      }
  
      get reads() {
          return this._reads;
      }
      set reads(reads) {
          this._reads=reads
      }
  
      get writes() {
          return this._writes;
      }
      set writes(writes) {
          this._writes = writes;
      }
  
      get storage() {
          return this._storage;
      }
      set storage(storage) {
          this._storage = storage;
      }
      get scale() {
          return this._scale;
      }
      set scale(scale) {
          this._scale=scale;
      }

      setInputsFromForm() {
        this.reads = document.getElementById('reads').value || 30000
        this.writes = document.getElementById('writes').value || 20000
        this.storage = document.getElementById('storage').value || 100
        this.scale = parseFloat(document.getElementById('scale').value) || 0.1

      }

    }



class App {
    constructor() {
    
      this._initState = false;
      this._inputs   = undefined;
      this._tableset = undefined;

    }
    get inputs() {
        return this._inputs;
    }
    set inputs(inputs){
        this._inputs = inputs;
    }

    get tableset() {
        return this._tableset;
    }

    set tableset(tableset) {
        this._tableset=tableset;
    }

    

    initTables(response) {
       if (response === undefined) return false;

       this.tableset = new Tableset(response);
       this.renderView(this.tableset);
       return true;
   }

  /*
   * replaces table with the current datasets
   */
  renderView() {
    if (this.tableset === undefined) return false;

    var tablesetBody = document.getElementById("tablesetBody");
    /* create it if it doesn't exist */
    if (!tablesetBody) {
      tablesetBody = document.createElement('div');
      tablesetBody.id = 'tablesetBody';
      document.getElementById('dataport').appendChild(tablesetBody);
    }
    /* could be more efficient than full div replace here */
    tablesetBody.innerHTML = this.tableset.toDiv();
    //this.pager.assignEvents();
    //this.pager.initState = true;
    return true;
  }

   /*
   * call python service
   */
  getEstimates() {
    let dataService = new PricingService();
    this.inputs.setInputsFromForm();
    dataService.getStreamData(this.inputs).then((response) => {
      this.initTables(response);

    }).catch((err) => {
      console.log(err);
    });
    //localStorage.setItem('search', this.currentSearch);
    return true;
  }

  /* 
   * 
   */
  init() {
    let appHTMLContainer = document.createElement('div');
    appHTMLContainer.id = 'app';
    appHTMLContainer.style.width = '800px';
    /* query form */
    let queryForm = document.createElement('div');
    queryForm.id = 'queryForm';
    queryForm.className = "container";
    queryForm.style.border = "1px solid black";

    //see constant above, could do this all in js...
    queryForm.innerHTML = mastHTML;

    /* init screen */
    appHTMLContainer.appendChild(queryForm);
    document.body.appendChild(appHTMLContainer);

    if (this._inputs === undefined) this.inputs = new Inputs()

  }

}

/* pager is the main content - twitch navigation tool */
var app = new App();

/* once all scripts, css and body are loaded, insert the search form */
window.onload = () => {
  app.init();
}