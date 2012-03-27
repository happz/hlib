"""
Mako templates

@version:                       1.0

@author:                        Milos Prchlik
@contact:                       U{happz@happz.cz}
@license:                       DPL (U{http://www.php-suit.com/dpl})
"""

import hlib
import hlib.ui.templates
import mako.exceptions
import mako.lookup
import mako.template
import os.path

class Template(hlib.ui.templates.Template):
  """
  Mako template class.

  Based on Mako template library U{http://www.makotemplates.org/}
  """

  def __init__(self, name, encoding = 'utf-8', indent = False):
    """
    Instantiate with C{Template(name, encoding = 'utf-8', indent = True)}

    @param name:                Name of template, filename, extension included.
    @type name:                 C{string}
    @param encoding:            Output encoding. Default is C{utf-8}.
    @type encoding:             C{string}
    @param indent:              Whether to output indented and clean output. Default C{True}.
    @type indent:               C{bool}
    """
    super(Template, self).__init__(name, encoding = encoding, indent = indent)

    # pylint: disable-msg=E1101
    self.loader = mako.lookup.TemplateLookup(directories = hlib.config.templates.template_dirs, module_directory = hlib.config.templates.tmp_dir, output_encoding = self.encoding, encoding_errors = self.encoding_errors, filesystem_checks = True, input_encoding = 'utf-8')

  def load(self, text = None):
    if text == None:
      self.template = self.loader.get_template(self.name)

    else:
      self.template = mako.template.Template(text = text, lookup = self.loader, input_encoding = self.encoding, output_encoding = self.encoding)

    return self

  def do_render(self):
    return self.template.render(**self.params)

  @staticmethod
  def render_error():
    return mako.exceptions.html_error_template().render()
