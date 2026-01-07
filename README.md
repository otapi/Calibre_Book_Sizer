# Calibre_Book_Sizer
A plugin for Calibre which adds a size indicator to titles of books based on their wordcounts. Compatible with ODPS Catalog reader of the KOReader (tested on Kobo Aura).
Requires a pre*filled #pages column by the Count Pages plugin.
## Setup
### Load the plugin in Calibre:
* Open Calibre.
* Go to Preferences → Advanced → Plugins.
* Click “Load plugin from file” and select your Calibre_Book_Sizer.zip.
* Accept the security warning.
### Add to toolbar:
* Go to Preferences → Interface → Toolbars & menus.
* Choose the main toolbar (where you want the button).
* Add “Book Sizer” to the toolbar.
* Apply and close.
## Usage
* Select one or more books in Calibre
* Click on the toolbar icon of the Book Sizer
## Debug
calibre-debug -g