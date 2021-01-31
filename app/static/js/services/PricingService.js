/*
 * Talks to Pricing Endpoint
 */
class PricingService {
  constructor() {
    //this._baseUrl = "http://localhost/pricing/lp/json/";
    this._baseUrl = "/pricing/lp/json/conf";
    this._headers = {
      accept: "application/json",
      clientId: "w3moe641p9cucblko66t42khea6rxk",
    };
    this._data = {};
    this._chunk = 50;
  }

  get chunk() { return this._chunk;}

  /*
   * wraps the json request in a promise, defaults offset to zero, fixed limit
   * limit should match chunk in app.js - so technically they should be in a <config>.js
   */
  getStreamData(inputs, offset=0) {
    //let _offset = (offset) ? offset : 0;
    let url = this._baseUrl //+ inputs.reads + '/' + inputs.writes + '/' + inputs.storage + '/' + inputs.scale
    return new Promise((resolve, reject) => {
      let xhr = new XMLHttpRequest();
      xhr.open('POST', url);
      /* inject required headers */
      xhr.setRequestHeader('Accept', this._headers.accept);
      xhr.setRequestHeader('Client-ID', this._headers.clientId);
      xhr.d
      xhr.send(JSON.stringify(inputs));
      xhr.onload = () => {
        if (xhr.status == 200) {
          this._data = JSON.parse(xhr.response); 
          resolve(this._data);
        } else {
          reject({status: this.status, statusText: xhr.statusText});
        }
      };
      xhr.onerror = () => {
        reject({status: this.status, statusText: xhr.statusText});
      };
    });
  }


}