from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog, question_dialog, demonstrate
from calibre.gui2 import open_url
from calibre.utils.config import JSONConfig

from PyQt5.Qt import QIcon

PLUGIN_NAME = 'Book Sizer'

# Simple config – you can make this a full config dialog later
plugin_prefs = JSONConfig('plugins/calibre_book_sizer')
plugin_prefs.setdefault('words_per_page', 300)

import logging
logger = logging.getLogger(__name__)


class BookSizerAction(InterfaceAction):

    name = PLUGIN_NAME

    # Icon, text, tooltip, and keyboard shortcut
    # action_spec: (text, icon, tooltip, keyboard shortcut)
    action_spec = (
        'Book Sizer',
        None,
        'Add size indicator to titles of selected books',
        None
    )

    def genesis(self):
        """
        Called by Calibre when the plugin is loaded.
        Set up the toolbar button and connect the signal.
        """
        icon = QIcon(self.load_icon())
        self.qaction.setIcon(icon)
        self.qaction.triggered.connect(self.run)

    def load_icon(self):
        """
        Load the plugin icon from the images folder in the ZIP.
        """
        # 'images/book_sizer.png' inside the plugin ZIP
        return self.load_resources('images/book_sizer.png')


    def build_new_title(self, title:str, pages:int) -> str:
        return title

    def _run_inner(self):
        logger.info("Book Sizer triggered")
        
        gui = self.gui
        db = gui.current_db

        # Get selected book ids
        rows = gui.library_view.selectionModel().selectedRows()
        if not rows:
            info_dialog(gui, PLUGIN_NAME, 'No books selected.', show=True)
            return

        logger.info(f"Selected {len(rows)} book(s)")
        book_ids = [gui.library_view.model().id(r.row()) for r in rows]

        # Check that the #pages custom column exists
        custom_cols = db.custom_column_labels()
        if 'pages' not in custom_cols:
            error_dialog(
                gui, PLUGIN_NAME,
                'Custom column "#pages" not found.\n'
                'Please create a custom column with label "pages" and fill it using the Count Pages plugin.',
                show=True
            )
            return

        #words_per_page = plugin_prefs['words_per_page']

        changed = 0
        for book_id in book_ids:
            logger.info(f"--------------------------------------------")
            logger.info(f"Processing book ID {book_id}")
            mi = db.get_metadata(book_id, index_is_id=True)

            # Fetch the #pages value from the metadata
            pages = mi.get('#pages', None)
            if pages is None:
                continue

            try:
                pages = float(pages)
            except (TypeError, ValueError):
                logger.info(f"Skipping book {book_id} due invalid #pages column: '{mi.title}'")
                continue

            logger.info(f"Updating title for book {book_id}: '{mi.title}'")
            # Update the title
            new_title = self.build_new_title(mi.title, pages)
            if new_title != mi.title:
                mi.title = new_title
                db.set_metadata(book_id, mi)
                changed += 1

        gui.library_view.model().refresh_ids(book_ids)

        info_dialog(
            gui,
            PLUGIN_NAME,
            f'Updated {changed} book title(s).',
            show=True
        )

    def run(self, *args):
        """
        Execute the main plugin logic when the toolbar button is clicked.
        """
        try:
            self._run_inner()
        except Exception as e:
            # Show error dialog in Calibre
            error_dialog(
                self.gui, PLUGIN_NAME,
                f'An error occurred:\n{e}',
                show=True
            )
