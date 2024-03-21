## Conversions
This folder contains ad-hoc conversions for updating and studying the static json files used by the simulation.    

Loosely, the 'outputs' folder is a staging area for json and csv files that end up in the 'static' folder of the simulation.  

Loosely, 'stocks_edit.xlsx' is a crude platform for editing these files. It contains a data model with the originals, and sheets
that are usesd to produce edited versions of these and export them to 'outputs'.

The procedure is to make a value copy of whatever is in the data model, put it in a separate sheet, edit it, and then export it using the 'excel to json' add-in.  

### We will work on:
* User-friendly format for the json files (eg with named foreign keys to make it clearer what is linked to what)
* Develop 'experimental'xlsx' as a front end for the simulation.  



