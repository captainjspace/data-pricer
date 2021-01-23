# Data Pricer

## First use case - Profile Storage

With one set of inputs get pricing output for 
* Datastore
* Bigtable
* Spanner

### Story
>the second time i went in to do pricing, i realized there were pricing patterns, applying similar options, same inputs, needing to get the calculations out simulatneously with shared tweakable inputs.  this is just quick attempt to get the basics in place.  with some hard coded formulas and fixed inputs.  

### Learnings from turning the dials.
* Datastore is best priced for big storage.  
* The node requirements 2TB per node for Spanner especially multi-region $3.0/node, drive cost high very fast.
* If persistance is low a higher ratio of io activity is at play Spanner and Bigtable shine
* If Single region is all that is required,  replicated Bigtable clusters offers power huge advantages if you are are willing to implement a node autoscaler.

---

## TODO
* clean node driver
* learn/fix repl calcs (bt)
* tune node capacity counts for io on bt and spanner, should run at 100%
* add deletes for ds
