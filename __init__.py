from calibre.customize import InterfaceActionBase

class BookSizerPlugin(InterfaceActionBase):
    name                = 'Book Sizer'
    description         = 'Adds a size indicator (based on pagecount) to book titles using the #pages column.'
    supported_platforms = ['windows', 'osx', 'linux']
    author              = 'otapi'
    version             = (1, 0, 0)
    minimum_calibre_version = (6, 0, 0)  # adjust if needed

    # This is the module path and class name of the actual plugin implementation.
    actual_plugin       = 'calibre_plugins.book_sizer.action:BookSizerAction'
