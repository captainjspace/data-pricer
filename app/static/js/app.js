'use strict';


/*
 * @filename App.js
 * Main application facade, wraps core functions, view controller
 */
class Inputs {

    constructor() {
        this._reads = 30000;
        this._writes = 20000;
        this._storage = 100
        this._scale = 0.0;  
        this._bt_discount_factor = 0.15;
        this._ds_discount_factor = {}
        this._spanner_discount_factor = 0.7;
        this._ioscale = 0.0;
      }
  
      get reads() {
          return this._reads;
      }
      set reads(reads) {
          this._reads=parseInt(reads) || 0;
      }
  
      get writes() {
          return this._writes;
      }
      set writes(writes) {
          this._writes = parseInt(writes) || 0;
      }
  
      get storage() {
          return this._storage;
      }
      set storage(storage) {
          this._storage = parseInt(storage) || 0;
      }
      get scale() {
          return this._scale;
      }
      set scale(scale) {
          this._scale=parseFloat(scale) || 0.0;
      }
      get ioscale() {
        return this._ioscale;
      }
      set ioscale(ioscale) {
        this._ioscale=parseFloat(ioscale) || 0.0;
      }
      get bt_discount_factor () {
        return this._bt_discount_factor
      }
      set bt_discount_factor (bt_discount_factor) {
        this._bt_discount_factor=1-parseFloat(bt_discount_factor) || 1
      }
      get ds_discount_factor() {
        return this._ds_discount_factor
      }

      set ds_discount_factor(ds_discount_factor) {
        //TODO: validate correct keyscd
        this._ds_discount_factor=ds_discount_factor
      }

      // get ds_reads_discount_factor() {
      //   return this._ds_discount_factor['reads'];
      // }
      // set ds_reads_discount_factor(ds_reads_discount_factor) {
      //   this.this._ds_discount_factor['reads']=1-parseFloat(ds_reads_discount_factor) || 0.0
      // }
      // get ds_writes_discount_factor() {
      //   return this._ds_discount_factor['writes'];
      // }
      // set ds_writes_discount_factor(ds_writes_discount_factor) {
      //   this.this._ds_discount_factor['writes']=1-parseFloat(ds_writes_discount_factor) || 0.0
      // }


      get spanner_discount_factor() {
        return this._spanner_discount_factor
      }
      set spanner_discount_factor(spanner_discount_factor) {
        this._spanner_discount_factor=1-parseFloat(spanner_discount_factor) || 1
      }

      get_exists(field) {
        var f = document.getElementById(field)
        return (f!=null)? 1-parseFloat(f.value) || 1 : 1
      }

      setInputsFromForm() {
        this.reads = document.getElementById('reads').value || 30000
        this.writes = document.getElementById('writes').value || 20000
        this.storage = document.getElementById('storage').value || 100
        this.scale = parseFloat(document.getElementById('scale').value || 0).toFixed(1) 
        this.ioscale = parseFloat(document.getElementById('ioscale').value || 0).toFixed(1) 
        this.bt_discount_factor = parseFloat(document.getElementById('bt_discount_factor').value || 0 ).toFixed(3) 
        this.spanner_discount_factor = parseFloat(document.getElementById('spanner_discount_factor').value || 0).toFixed(3) 

        this.ds_discount_factor['reads'] = this.get_exists('ds_reads_discount_factor')
        this.ds_discount_factor['writes'] = this.get_exists('ds_writes_discount_factor')
        this.ds_discount_factor['deletes'] = this.get_exists('ds_deletes_discount_factor')
        this.ds_discount_factor['storage'] = this.get_exists('ds_storage_discount_factor')
      
      }
      
      getData() {
        return {
        'reads': this.reads,
        'writes': this.writes,
        'storage': this.storage,
        'scale': this.scale,
        'ioscale': this.ioscale,
        'bt_discount_factor': this.bt_discount_factor,
        'ds_discount_factor': this.ds_discount_factor,
        'spanner_discount_factor': this.spanner_discount_factor
        }
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
    tablesetBody.innerHTML = this.tableset.renderView();
    this.assignCopyEvent()
    return true;
  }
  
  assignCopyEvent() {
    document.getElementById("Measure").childNodes.forEach( (cell) => {
      cell.addEventListener('click', function (e) {
        app.tableset.copyToClipboard();
      })
    })
  }
   /*
   * call python service
   */
  getEstimates() {
    let dataService = new PricingService();
    this.inputs.setInputsFromForm();
    dataService.getStreamData(this.inputs.getData()).then((response) => {
      this.initTables(response);
    }).catch((err) => {
      console.log(err);
    });
    localStorage.setItem('search', JSON.stringify(this.inputs));
    
    return true;
  }

  /* 
   * 
   */
  init() {
    let appHTMLContainer = document.createElement('div');
    appHTMLContainer.id = 'app';
    appHTMLContainer.style.width = '1200px';
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


    // assigned keypress events
    let inputs = document.querySelectorAll('.form-field__input');
    inputs.forEach((input) => {
       input.addEventListener('keypress', function(e) {
          if (e.key === 'Enter') app.getEstimates();
       }
       )
      }
    );
    
    let l_inputs = localStorage.getItem('search');
    console.log(l_inputs);
    if (this._inputs === undefined) this.inputs = new Inputs()

  }

}

/* pager is the main content - twitch navigation tool */
var app = new App();

/* once all scripts, css and body are loaded, insert the search form */
window.onload = () => {
  app.init();
  app.getEstimates();
}

const mastHTML=`<div class="gclogo"><img id="gclogo" src="/static/img/cloud-logo.svg"></div>
<div id="inputBox" class="flex-column">

    <div class="flex-row">

        <div class="form-field z3">
            <div class="form-field__control">
                <input type="text" id="reads" class="form-field__input" placeholder="30000" autofocus />
                <label for="reads" class="form-field__label">Reads per Second</label>
                <div class="form-field__bar"></div>
            </div>
        </div>

        <div class="form-field z3">
            <div class="form-field__control">
                <input type="text" id="writes" class="form-field__input" placeholder="20000" />
                <label for="writes" class="form-field__label">Writes per Second</label>
                <div class="form-field__bar"></div>
            </div>
        </div>

        <div class="form-field z3">
            <div class="form-field__control">
                <input type="text" id="storage" class="form-field__input" placeholder="100" />
                <label for="storage" class="form-field__label">Storage (TB)</label>
                <div class="form-field__bar"></div>
            </div>
        </div>

    </div>

    <div class="flex-row">

        <div class="form-field z4">
            <div class="form-field__control">
                <input type="text" id="ioscale" class="form-field__input" placeholder="0.0" />
                <label for="ioscale" class="form-field__label">Projected I/0 Growth Scale (0.0-1.0)</label>
                <div class="form-field__bar"></div>
            </div>
        </div>

        <div class="form-field z4">
            <div class="form-field__control">
                <input type="text" id="scale" class="form-field__input" placeholder="0.0" />
                <label for="scale" class="form-field__label">Project Storage Growth Scale (0.0-1.0)</label>
                <div class="form-field__bar"></div>
            </div>
        </div>

        <div class="form-field z4">
            <div class="form-field__control">
                <input type="text" id="bt_discount_factor" class="form-field__input" placeholder="0.0" />
                <label for="bt_discount_factor" class="form-field__label">Bigtable Discount(%)</label>
                <div class="form-field__bar"></div>
            </div>
        </div>

        <div class="form-field z4">
            <div class="form-field__control">
                <input type="text" id="spanner_discount_factor" class="form-field__input" placeholder="0.0" />
                <label for="spanner_discount_factor" class="form-field__label">Spanner Discount(%)</label>
                <div class="form-field__bar"></div>
            </div>
        </div>

    </div>


    <div class="flex-row">

        <div class="form-field z4">
            <div class="form-field__control">
                <input type="text" id="ds_reads_discount_factor" class="form-field__input" placeholder="0.0" />
                <label for="ds_reads_discount_factor" class="form-field__label">Datastore Reads Discount(%)</label>
                <div class="form-field__bar"></div>
            </div>
        </div>
        <div class="form-field z4">
            <div class="form-field__control">
                <input type="text" id="ds_writes_discount_factor" class="form-field__input" placeholder="0.0" />
                <label for="ds_writes_discount_factor" class="form-field__label">Datastore Write Discount(%)</label>
                <div class="form-field__bar"></div>
            </div>
        </div>

        <div class="form-field z4">
            <div class="form-field__control">
                <input type="text" id="ds_deletes_discount_factor" class="form-field__input" placeholder="0.0" />
                <label for="ds_deletes_discount_factor" class="form-field__label">Datastore Deletes Discount(%)</label>
                <div class="form-field__bar"></div>
            </div>
        </div>
        <div class="form-field z4">
            <div class="form-field__control">
                <input type="text" id="ds_storage_discount_factor" class="form-field__input" placeholder="0.0" />
                <label for="ds_storage_discount_factor" class="form-field__label">Datastore Storage Discount(%)</label>
                <div class="form-field__bar"></div>
            </div>
        </div>

    </div>
</div>

<div id="dataport">
</div>`;