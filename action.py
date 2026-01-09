from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog, question_dialog
from calibre_plugins.modify_epub.common_icons import set_plugin_icon_resources, get_icon
from calibre.gui2 import open_url
from calibre.utils.config import JSONConfig

from PyQt5.Qt import QIcon
import re

PLUGIN_ICONS = ['images/book_sizer.png']

import logging
logger = logging.getLogger(__name__)


class BookSizerAction(InterfaceAction):

    name = 'Book Sizer'

    # Icon, text, tooltip, and keyboard shortcut
    # action_spec: (text, icon, tooltip, keyboard shortcut)

    action_spec = (_('Book Sizer'), None, _('Add size indicator to titles of selected books'), ())
    action_type = 'current'

    def genesis(self):
        """
        Called by Calibre when the plugin is loaded.
        Set up the toolbar button and connect the signal.
        """
        icon_resources = self.load_resources(PLUGIN_ICONS)
        set_plugin_icon_resources(self.name, icon_resources)
        self.qaction.setIcon(get_icon(PLUGIN_ICONS[0]))
        self.qaction.triggered.connect(self.run)

    def build_new_title(self, title:str, pages:int) -> str:
        title = (re.sub(r'\[\d+\]$', '', title)).strip()
        title = (re.sub(r'[\x00-\x1F\x7F]', '', title))
        title = (re.sub(r'[\u200B\u200C\u200D\uFEFF]', '', title))
        
        title = f"{title} [{str(int(pages))}]"
        return title

    def about_to_show_menu(self):
        self.rebuild_menus()
        
    def _run_inner(self):
        logger.info("Book Sizer triggered")
        
        gui = self.gui
        db = gui.current_db

        # Get selected book ids
        rows = gui.library_view.selectionModel().selectedRows()
        if not rows:
            info_dialog(gui, self.name, 'No books selected.', show=True)
            return

        logger.info(f"Selected {len(rows)} book(s)")
        book_ids = [gui.library_view.model().id(r.row()) for r in rows]

        # Check that the #pages custom column exists
        custom_cols = db.field_metadata.custom_field_metadata()
        if '#pages' not in custom_cols:
            error_dialog(
                gui, self.name,
                'Custom column "#pages" not found.\n'
                'Please create a custom column with label "pages" and fill it using the Count Pages plugin.',
                show=True
            )
            return

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
            self.name,
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
                self.gui, self.name,
                f'An error occurred:\n{e}',
                show=True
            )
