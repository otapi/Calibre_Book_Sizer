from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog
from calibre_plugins.modify_epub.common_icons import set_plugin_icon_resources, get_icon
from calibre.utils.config import JSONConfig

from PyQt5.Qt import QIcon
import re
import logging

logger = logging.getLogger(__name__)

PLUGIN_ICONS = ['images/book_sizer.png']


# ---------------------------------------------------------------------------
# Background job worker function
# ---------------------------------------------------------------------------

def do_book_sizer_job(book_ids, db_path, **kwargs):
    """
    Runs inside calibre's background job system.
    Returns a dict: {book_id: new_title}
    """
    from calibre.library import db as db_module
    import re

    log = kwargs.get('log')          # progress + logging
    abort = kwargs.get('abort')      # cancellation support (optional)
    total = len(book_ids)
    processed = 0

    db = db_module(db_path)
    results = {}

    for book_id in book_ids:
        processed += 1

        # Allow user to cancel the job
        if abort and abort.is_set():
            if log:
                log("Job aborted by user.")
            break

        # --- progress update ---
        if log:
            pct = int((processed / total) * 100)
            log.report_progress(pct)

        mi = db.get_metadata(book_id, index_is_id=True)

        # --- log the title being processed ---

        pages = mi.get('#pages', None)
        if pages is None:
            if log:
                log(f"Skipped as page number is missing from #pages: {mi.title}")
            continue

        try:
            pages = float(pages)
        except Exception as r:
            if log: 
                log(f"Invalid #pages value for book ID {mi.title}: {pages}")
            continue

        if log: 
           log(f"Processing {mi.title}: {pages}")

        # Clean title
        title = mi.title
        title = (re.sub(r'\[\d+\]$', '', title)).strip()
        title = (re.sub(r'[\x00-\x1F\x7F]', '', title))
        title = (re.sub(r'[\u200B\u200C\u200D\uFEFF]', '', title))

        new_title = f"{title} [{int(pages)}]"

        if new_title != mi.title:
            results[book_id] = new_title

    return results




# ---------------------------------------------------------------------------
# Main plugin action
# ---------------------------------------------------------------------------

class BookSizerAction(InterfaceAction):

    name = 'Book Sizer'
    action_spec = (
        _('Book Sizer'),
        None,
        _('Add size indicator to titles of selected books'),
        ()
    )
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

    # ----------------------------------------------------------------------

    def run(self, *args):
        """
        Execute the main plugin logic when the toolbar button is clicked.
        """
        try:
            self._queue_job()
        except Exception as e:
            error_dialog(
                self.gui, self.name,
                f'An error occurred:\n{e}',
                show=True
            )

    # ----------------------------------------------------------------------

    def _queue_job(self):
        gui = self.gui
        db = gui.current_db

        # Get selected book ids
        rows = gui.library_view.selectionModel().selectedRows()
        if not rows:
            info_dialog(gui, self.name, 'No books selected.', show=True)
            return

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

        # Queue background job
        job = gui.job_manager.run_job(
            self.Dispatcher(self._job_finished),
            'arbitrary_n',
            args=[
                'calibre_plugins.book_sizer.action',  # module path
                'do_book_sizer_job',                  # function name
                (book_ids, db.library_path)           # arguments
            ],
            description=_('Updating book titles')
        )

        gui.status_bar.show_message(
            _('Updating %d books…') % len(book_ids)
        )

    # ----------------------------------------------------------------------

    def _job_finished(self, job):
        """
        Called when the background job completes.
        """
        if job.failed:
            return self.gui.job_exception(job, dialog_title=_('Book Sizer Failed'))

        results = job.result  # {book_id: new_title}

        if not results:
            info_dialog(self.gui, self.name,
                        'No titles needed updating.', show=True)
            return

        db = self.gui.current_db

        # Apply metadata updates
        for book_id, new_title in results.items():
            mi = db.get_metadata(book_id, index_is_id=True)
            mi.title = new_title
            db.set_metadata(book_id, mi)

        # Refresh GUI
        self.gui.library_view.model().refresh_ids(list(results.keys()))

        info_dialog(
            self.gui,
            self.name,
            f'Updated {len(results)} book title(s).',
            show=True
        )
