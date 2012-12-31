#
# Namespaces
#
window.hlib = window.hlib or {}
window.hlib.templates = window.hlib.templates or {}

#
# Classes
#

class window.hlib.MessageDialog
  constructor:			(eid) ->
    if not eid
      eid = window.hlib.OPTS.message_dialog

    @eid = eid
    @classes = null

    $('.modal-footer button').click () ->
      window.hlib.MESSAGE.hide()
      return false

  show:				(label, msg, beforeClose) ->
    $(@eid + ' .modal-header h3').html ''
    if label
      $(@eid + ' .modal-header h3').html window.hlib._g label

    $(@eid + ' .modal-body p').html ''
    if msg
      $(@eid + ' .modal-body p').html msg

    if beforeClose
      eid = @eid

      beforeClose_handler = () ->
        beforeClose()

      $(eid).off 'hidden', beforeClose_handler

    $(@eid).removeClass 'bg-color-red bg-color-green'
    if @classes
      $(@eid).addClass @classes

    $(@eid).modal 'show'

  hide:				() ->
    $(@eid).modal 'hide'
    $('.modal-backdrop').remove()

class window.hlib.ErrorDialog extends window.hlib.MessageDialog
  constructor:			(eid) ->
    super(eid)

    @classes = 'bg-color-red'

class window.hlib.InfoDialog extends window.hlib.MessageDialog
  constructor:			(eid) ->
    super(eid)

    @classes = 'bg-color-green'

class window.hlib.WorkingDialog extends window.hlib.MessageDialog
  constructor:			(eid) ->
    super(eid)

  show:				() ->
    super 'Your request is being processed by our hamsters', window.hlib._g 'If it takes too long, poke our admins <a href="irc://ellen.czn.cz/osadnici">here</a>.'

class window.hlib.Ajax
  constructor:		(opts) ->
    _ajax = @

    if not opts.hasOwnProperty 'data'
      opts.data = {}
    if not opts.hasOwnProperty 'keep_focus'
      opts.keep_focus = false
    if not opts.hasOwnProperty 'show_spinner'
      opts.show_spinner = true

    focus_elements = $(document.activeElement)

    handle_ajax_error = (response, jqXHR, textStatus, errorThrown) ->
      h = window.hlib.get_handler opts, 'error', window.hlib.ajax_default_handlers
      if h
        h response, _ajax
        return

      console.log 'error called', textStatus
      console.log jqXHR, errorThrown
      window.hlib.ERROR.show 'Bad things are all around us. Check JS console'

    $.ajax
      dataType:		'json'
      type:		'POST'
      url:		opts.url
      data:		opts.data
      cache:		false
      timeout:		10000
      async:		true

      statusCode:
        500:		() ->
          window.hlib.ERROR.show 'Server unavailable', 'Oh no! Server suddenly went away. Be sure we are all freaking out - take a break, get a coffee, and try again in 5 minutes or so.'

      beforeSend:	() ->
        if opts.show_spinner == true
          window.hlib.WORKING.show()

      complete:			(jqXHR, textStatus) ->
        response = $.parseJSON jqXHR.responseText

        if textStatus == 'success'
          handler_name = 'h' + response.status

          h = window.hlib.get_handler opts, handler_name, window.hlib.ajax_default_handlers
          if h
            h response, _ajax

            if opts.keep_focus and focus_elements[0] and focus_elements[0].id
              $('#' + focus_elements[0].id).focus()

            return

          window.hlib.ERROR.show 'No handler for response status', 'Something is rotten in the state of Denmark... There is no handler for response status ' + response.status

        else
          handle_ajax_error response, jqXHR, textStatus, errorThrown

      error:			(jqXHR, textStatus, errorThrown) ->
        response = $.parseJSON jqXHR.responseText
        handle_ajax_error response, jqXHR, textStatus, errorThrown

class window.hlib.Pager
  constructor:		(@opts) ->
    _pager = @

    @id_prefix	= opts.id_prefix
    @url	= opts.url
    @eid	= opts.eid
    @data	= opts.data
    @template	= opts.template

    @start	= opts.start
    @length	= opts.length

    @items	= null

    $(@eid + ' .' + @id_prefix + '-first').click () ->
      _pager.first()
      return false

    $(@eid + ' .' + @id_prefix + '-last').click () ->
      _pager.last()
      return false

    $(@eid + ' .' + @id_prefix + '-prev').click () ->
      _pager.prev()
      return false

    $(@eid + ' .' + @id_prefix + '-next').click () ->
      _pager.next()
      return false

  refresh:		() ->
    _pager = @

    data =
      start:		_pager.start
      length:		_pager.length

    $.extend data, _pager.data

    window.hlib.Ajax
      url:		_pager.url
      data:		data
      handlers:
        h200:		(response, _ajax) ->
          _pager.items = response.page.cnt_total

          $(_pager.eid + ' tbody').html ''
          $(_pager.eid + ' tbody').append _pager.template record for record in response.page.records

          $(_pager.eid + ' .' + _pager.id_prefix + '-position').html '' + (_pager.start + 1) + '. - ' + (Math.min _pager.items, _pager.start + response.page.cnt_display) + '. z ' + _pager.items

          if _pager.opts.hasOwnProperty 'after_refresh'
            _pager.opts.after_refresh response, _pager

          window.hlib.MESSAGE.hide()

  first:		() ->
    @start = 0
    @refresh()

  last:			() ->
    @start = (Math.floor @items / @length) * @length
    @refresh()

  prev:			() ->
    @start = Math.max 0, @start - @length
    @refresh()

  next:			() ->
    @start = Math.min @items - 1, @start + @length
    @refresh()

class window.hlib.FormField
  constructor:	(@fid, @form) ->
    @on_enabled = null
    @on_disable = null

  mark_error:		() ->
    $(@fid).parent().parent().addClass('error').focus().val('')

    @form.last_invalid_field = @
    @

  unmark_error:	() ->
    $(@fid).parent().parent().removeClass 'error'
    $(@fid).focus()

    @form.last_invalid_field = null
    @

  enable:		(handler) ->
    if handler
      @on_enable = handler

    else
      $(@fid).removeAttr 'disabled'
      $(@fid).removeAttr 'placeholder'

      if @on_enable
        @on_enable @

    @

  disable:		(handler) ->
    if handler
      @on_disable = handler

    else
      $(@fid).attr 'disabled', 'disabled'

      if @on_disable
        @on_disable @

    @

  empty:		() ->
    $(@fid).html ''
    @

  placeholder:			(text) ->
    if text
      if $(@fid).prop('tagName') == 'SELECT'
        $(@fid).html('').prepend('<option value="" disabled="disabled">' + text + '</option>').val('')
      else
        $(@fid).attr('placeholder', text).val('')
      return @

    else
      $(@fid).attr 'placeholder'

  content:		(html) ->
    if html
      $(@fid).html html
      return @

    else
      return $(@fid).html()

  value:		(val) ->
    if val
      $(@fid).val val
      return @

    else
      return $(@fid).val()

  hide:			() ->
    $(@fid).hide()
    @

  show:			() ->
    $(@fid).show()
    @

class window.hlib.Form
  class FormInfo
    constructor:	(@form) ->
      @eid = @form.fid + ' .form-info'

    _show: (msg, title, cls) ->
      $(@eid + ' strong').html ''
      $(@eid).removeClass 'alert-error'
      $(@eid).removeClass 'alert-success'

      $(@form.fid + ' p').html window.hlib._g msg

      $(@eid + ' strong').html ''
      if title
        $(@eid + ' strong').html window.hlib._g title

      if cls
        $(@eid).addClass cls

      $(@eid).show()

    _hide: () ->
      $(@eid).hide()

    error:			(msg) ->
      this._show msg, 'Error!', 'alert-error'

    success:			(msg, dont_fade) ->
      this._show msg, '', 'alert-success'

      if dont_fade
        return

      $(@eid).fadeOut 3000

  clear:		() ->
    $(@field_id name).val '' for name in @opts.clear_fields

  constructor: (@opts) ->
    @fid = '#' + opts.fid + '_form'
    @info = new FormInfo(@)
    @fields = {}

    if not opts.hasOwnProperty 'clear_fields'
      opts.clear_fields = []

    if not opts.hasOwnProperty 'disable_fields'
      opts.disable_fields = []

    if not opts.hasOwnProperty 'submit_empty'
      opts.submit_empty = false

    @opts = opts
    _form = @

    @form_opts =
      dataType:		'json'
      success:	(response) ->
        window.hlib.MESSAGE.hide()

        _form.clear()

        if response.status != 200 and opts.hasOwnProperty('refill') and opts.refill == true and response.form.hasOwnProperty('orig_fields')
          $(_form.field_id key).val value for own key, value of response.form.orig_fields

        handler_name = 's' + response.status

        h = window.hlib.get_handler opts, handler_name, window.hlib.form_default_handlers
        if h
          h response, _form
          return

        window.hlib.ERROR.show 'No handler for response status', 'Something is rotten in the state of Denmark... There is no handler for response status ' + response.status

      beforeSerialize:		(f, o) ->
        if opts.submit_empty != true
          f.find(':input[value=""]').attr 'disabled', 'disabled'

        return true

      beforeSubmit:             (a, f, o) ->
        f.find(':input[value=""]').removeAttr 'disabled'

        _form.info._hide()
        if _form.last_invalid_field
          _form.last_invalid_field.unmark_error()

        window.hlib.WORKING.show()
        return true

    $(@fid).live 'submit', (event) ->
      event.preventDefault()

      $(_form.fid).ajaxSubmit _form.form_opts

      return false

    @clear()

    if opts.hasOwnProperty 'focus'
      $(@field_id opts.focus).focus()

    (@field f).disable() for f in opts.disable_fields

  submit:		() ->
    $(@fid).ajaxSubmit @form_opts

  field_id:		(name) ->
    '#' + @opts.fid + '_' + name

  field:		(name) ->
    if not @fields.hasOwnProperty(name)
      @fields[name] = new window.hlib.FormField (@field_id name), @

    return @fields[name]

  invalid_field:	(response) ->
    if not response.form.hasOwnProperty 'invalid_field'
      return null

    return @field response.form.invalid_field

  update_fields:	(fields) ->
    $(@field_id f).val v for f, v of fields

#
# Methods
#
String.prototype.format = () ->
  args = arguments;
  return @replace /\{(\d+)\}/g, (m, n) -> return args[n]

String.prototype.capitalize = () ->
  return @charAt(0).toUpperCase() + this.slice 1

window.hlib.OPTS		= null
window.hlib.INFO		= null
window.hlib.ERROR		= null
window.hlib.WORKING		= null

window.hlib.trace = () ->
  trace = printStackTrace()
  console.log trace.join '\n'

window.hlib._g = (s) ->
  if s.length <= 0
    return ''

  if window.settlers.i18n and window.settlers.i18n.tokens and window.settlers.i18n.tokens.hasOwnProperty s
    return window.settlers.i18n.tokens[s]

  console.log 'Unknown token: ' + s
#  window.hlib.trace()
  return s

window.hlib.disable = (fid) ->
  if not $('#' + fid).hasClass 'disabled'
    $('#' + fid).addClass 'disabled'

window.hlib.enable = (fid) ->
  $('#' + fid).removeClass 'disabled'

window.hlib.enableIcon = (sel, callback) ->
  $(sel).removeAttr 'disabled'
  $(sel).unbind 'click'
  $(sel).click () ->
    callback()
    return false

window.hlib.disableIcon = (sel) ->
  $('a[rel=tooltip]').tooltip 'hide'
  $('button[rel=tooltip]').tooltip 'hide'

  $(sel).attr 'disabled', 'disabled'
  $(sel).unbind 'click'
  $(sel).click () ->
    return false

window.hlib.dump = (arr, level) ->
  dumped_text = ''

  if !level
    level = 0

  level_padding = ''
  k = level + 1
  level_padding += '    ' for j in [0...k]

  if typeof(arr) == 'object'
    for k, v of arr
      if typeof(value) == 'object'
        dumped_text += level_padding + "'" + k + "' ...\n"
        dumped_text += this.dump v, level + 1
      else
        dumped_text += level_padding + "'" + k + "' => '" + v + "'\n"
  else
    dumped_text = '=== ' + arr + ' ===(' + typeof(arr) + ')'

  return dumped_text

window.hlib.clone = (obj) ->
  if not obj? or typeof obj isnt 'object'
    return obj

  newInstance = new obj.constructor()

  for key of obj
    newInstance[key] = clone obj[key]

  return newInstance

window.hlib.redirect = (url) ->
  window.location.replace url
  false

window.hlib.setTitle = (msg) ->
  document.title = msg

window.hlib.get_handler = (table_parent, handler_name, defaults) ->
  if table_parent.hasOwnProperty 'handlers'
    table = table_parent.handlers

    if table.hasOwnProperty handler_name
      return table[handler_name]

  if defaults.hasOwnProperty handler_name
    return defaults[handler_name]

  return false

window.hlib.format_string = (str, params) ->
  __per_param = (name, value) ->
    str = str.replace '%(' + name + ')s', value

  __per_param name, value for own name, value of params
  return str

window.hlib.format_error = (error) ->
  return window.hlib.format_string (window.hlib._g error.message), error.params

window.hlib.error = (label, error, beforeClose) ->
  window.hlib.ERROR.show (window.hlib._g label), (window.hlib.format_error error), beforeClose

window.hlib.form_default_handlers =
  # Everything is all right
  s200:	(response, form) ->
    if response.form and response.form.hasOwnProperty 'updated_fields'
      form.update_fields response.form.updated_fields

    form.info.success 'Successfully changed'

  # Redirect
  s303:		(response, form) ->
    window.hlib.redirect response.redirect.url

  # Bad Request - empty fields, invalid values, typos, ...
  s400:				(response, form) ->
    form.invalid_field(response).mark_error()
    form.info.error window.hlib.format_error response.error

  # Unauthorized - wrong password, ACL violations, ...
  s401:       (response, form) ->
    window.hlib.error 'Unauthorized', response.error

  # Conflicting errors - impossible requests, joining already joined games, etc...
  s402:       (response, form) ->
    window.hlib.error 'Conflict error', response.error

  # Invalid (not malformed!) input - duplicit names, unknown names etc.
  s403:       (response, form) ->
    form.invalid_field(response).mark_error()
    form.info.error window.hlib.format_error response.error

  # Internal server error
  s500:		(response, form) ->
    window.hlib.error 'Internal error', response.error

window.hlib.ajax_default_handlers =
  # Redirect
  h303:		(response, ajax) ->
    window.hlib.redirect response.redirect.url

  # Invalid (not malformed!) input - duplicit names, unknown names etc.
  h403:		(response, ajax) ->
    window.hlib.error '', response.error

  # Internal server error
  h500:		(response, ajax) ->
    window.hlib.error 'Internal error', response.error

window.hlib.setup = (opts) ->
  window.hlib.OPTS = opts

  window.hlib.MESSAGE = new window.hlib.MessageDialog opts.message_dialog
  window.hlib.INFO = new window.hlib.InfoDialog opts.message_dialog
  window.hlib.ERROR = new window.hlib.ErrorDialog opts.message_dialog
  window.hlib.WORKING = new window.hlib.WorkingDialog opts.message_dialog

  $(opts.message_dialog).modal
    show:			false
