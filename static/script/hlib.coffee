#
# Namespaces
#
window.hlib = window.hlib or {}
window.hlib.templates = window.hlib.templates or {}

#
# Classes
#
class window.hlib.Info
  constructor: () ->
    @eid = window.hlib.OPTS.info_dialog.eid
    @visible = false

  _setup: (tmpl, data, cls, opts) ->
    $(@eid).dialog
      closeText:	'Close'
      autoOpen:		false
      height:		150
      modal:		true

    if opts?
      $(@eid).dialog 'option', opts

    content = window.hlib.render tmpl, data
    $(@eid).html content

    $(@eid + ' div.right input[type="button"]').click () ->
      window.hlib.INFO._hide()

  _show: () ->
    $(@eid).dialog 'open'
    @visible = true

  _hide: () ->
    if not @visible
      return

    $(@eid).dialog 'close'
    $(@eid).dialog 'destroy'

    @visible = false

  success: (msg, beforeClose) ->
    data =
      msg:	msg

    this._setup window.hlib.templates.info_dialog.success, data, 'formee-msg-success',
      beforeClose:	beforeClose

    this._show()

  working: (msg) ->
    data =
      msg:	null

    this._setup window.hlib.templates.info_dialog.working, data, 'formee-msg-info'
    this._show()

  error: (msg, beforeClose) ->
    data =
      msg:	msg

    this._setup window.hlib.templates.info_dialog.error, data, 'formee-msg-error',
      beforeClose:	beforeClose

    this._show()

class window.hlib.Ajax
  constructor:		(opts) ->
    _ajax = @

    if not opts.hasOwnProperty 'async'
      opts.async = false
    if not opts.hasOwnProperty 'data'
      opts.data = {}
    if not opts.hasOwnProperty 'keep_focus'
      opts.keep_focus = false

    focus_elements = $(document.activeElement)

    $.ajax
      dataType:		'json'
      type:		'POST'
      url:		opts.url
      async:		opts.async
      data:		opts.data
      cache:		false
      timeout:		10000

      statusCode:
        500:		() ->
          console.log 'error called'
          window.hlib.INFO.error 'Server unavailable'

      beforeSend:	() ->
        window.hlib.INFO.working()

      success:		(response) ->
        handler_name = 'h' + response.status

        h = window.hlib.get_handler opts, handler_name, window.hlib.ajax_default_handlers
        if h
          h response, _ajax

          if opts.keep_focus and focus_elements[0] and focus_elements[0].id
            $('#' + focus_elements[0].id).focus()

          return

        window.hlib.INFO.error 'No handler for response status ' + response.status

      error:		(request, msg, e) ->
        console.log 'error called', e
        window.hlib.INFO.error msg

class window.hlib.Pager
  constructor:		(opts) ->
    _pager = @

    @id_prefix	= opts.id_prefix
    @url	= opts.url
    @eid	= opts.eid
    @data	= opts.data
    @template	= opts.template

    @start	= opts.start
    @length	= opts.length
    @items	= null

    $(@eid + ' span.' + @id_prefix + '-first').click () ->
      _pager.first()
      return false

    $(@eid + ' span.' + @id_prefix + '-last').click () ->
      _pager.last()
      return false

    $(@eid + ' span.' + @id_prefix + '-prev').click () ->
      _pager.prev()
      return false

    $(@eid + ' span.' + @id_prefix + '-next').click () ->
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
          $(_pager.eid + ' tbody').append window.hlib.render _pager.template, record for record in response.page.records

          $(_pager.eid + ' span.' + _pager.id_prefix + '-position').html '' + (_pager.start + 1) + '. - ' + (Math.min _pager.items, _pager.start + response.page.cnt_display) + '. z ' + _pager.items

          window.hlib.INFO._hide()

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

class window.hlib.Form
  class FormField
    constructor:	(@fid) ->

    mark_error:		() ->
      $(@fid).focus()
      $(@fid).addClass 'formee-error'
      $(@fid).val('')

    unmark_error:	() ->
      $(@fid).removeClass 'formee-error'
      $(@fid).focus()

  class FormInfo
    constructor:	(form) ->
      @eid = form.fid + ' .form-forminfo'

    _show: (msg, cls) ->
      $(@eid).html '<label>' + msg + '</label>'
      $(@eid).removeClass 'formee-msg-success formee-msg-error formee-msg-info'
      $(@eid).addClass cls
      $(@eid).css 'display', 'block'
      $(@eid).fadeOut 3000

    _hide: () ->
      $(@eid).css 'display', 'none'

    success: (msg) ->
      this._show msg, 'formee-msg-success'

  clear:		() ->
    $('#' + @opts.fid + '_' + name).val '' for name in @opts.clear_fields

  constructor: (opts) ->
    @opts = opts

    @fid = '#' + opts.fid + '_form'
    @info = new FormInfo(@)

    if not opts.hasOwnProperty 'clear_fields'
      opts.clear_fields = []

    if not opts.hasOwnProperty 'submit_empty'
      opts.submit_empty = false

    _form = @

    $(@fid).ajaxForm
      dataType:		'json'
      success:	(response) ->
        window.hlib.INFO._hide()

        _form.clear()

        if response.status != 200 and opts.hasOwnProperty('refill') and opts.refill == true and response.form.hasOwnProperty('orig_fields')
          $(_form.field_id key).val value for own key, value of response.form.orig_fields

        handler_name = 's' + response.status

        h = window.hlib.get_handler opts, handler_name, window.hlib.form_default_handlers
        if h
          h response, _form
          return

        window.hlib.INFO.error 'No handler for response status ' + response.status

      beforeSerialize:		(f, o) ->
        if opts.submit_empty != true
          f.find(':input[value=""]').attr 'disabled', 'disabled'

        return true

      beforeSubmit:             (a, f, o) ->
        f.find(':input[value=""]').removeAttr 'disabled'

        window.hlib.INFO.working()
        return true

    @clear()

    if opts.hasOwnProperty 'focus'
      $(@field_id opts.focus).focus()

  field_id:		(name) ->
    '#' + @opts.fid + '_' + name

  invalid_field:	(response) ->
    if not response.form.hasOwnProperty 'invalid_field'
      return null

    new FormField @field_id response.form.invalid_field

  update_fields:	(fields) ->
    $(@field_id f).val v for f, v of fields

#
# Methods
#
String.prototype.format = () ->
  args = arguments;
  return @replace /\{(\d+)\}/g, (m, n) -> return args[n]

window.hlib.templates.info_dialog =
  error:        '
    <div class="formee-msg-error">
      <label>{{msg}}</label>
      <div class="right"><input type="button" value="Ok" /></div>
    </div>'
  working:      '
    <div class="formee-msg-info">
      <img src="/static/images/spinner.gif" alt="" class="ajax_spinner" />
      <label>Your request is being processed by our hamsters.</label>
      If it takes too long, poke our admins <a href="irc://ellen.czn.cz/osadnici">here</a>.
    </div>'
  success:      '
    <div class="formee-msg-success">
      <label>{{msg}}</label>
      <div class="right"><input type="button" value="Ok" /></div>
    </div>'

window.hlib.OPTS =		null
window.hlib.INFO =		null

window.hlib._g = (s) ->
  if window.settlers.i18n and window.settlers.i18n.tokens and s in window.settlers.i18n.tokens
    return window.settlers.i18n.tokens[s]

  return s

window.hlib.disable = (fid) ->
  if not $('#' + fid).hasClass 'disabled'
    $('#' + fid).addClass 'disabled'

window.hlib.enable = (fid) ->
  $('#' + fid).removeClass 'disabled'

window.hlib.enableIcon = (sel, callback) ->
  $(sel).removeClass 'icon-disabled'
  $(sel).unbind 'click'
  $(sel).click () ->
    callback()
    return false

window.hlib.disableIcon = (sel) ->
  $(sel).removeClass 'icon-disabled'
  $(sel).addClass 'icon-disabled'
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
  window.location = url

window.hlib.setTitle = (msg) ->
  document.title = msg

window.hlib.render = (tmpl, data) ->
  Mustache.to_html(tmpl, data)

window.hlib.get_handler = (table_parent, handler_name, defaults) ->
  if table_parent.hasOwnProperty 'handlers'
    table = table_parent.handlers

    if table.hasOwnProperty handler_name
      return table[handler_name]

  if defaults.hasOwnProperty handler_name
    return defaults[handler_name]

  return false

window.hlib.error = (error, after) ->
  msg = error.message

  __per_param = (name, value) ->
    msg = msg.replace '%(' + name + ')s', value

  __per_param name, value for own name, value of error.params

  window.hlib.INFO.error msg, after

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
  s400:       (response, form) ->
    field = form.invalid_field(response)
    field.mark_error()

    window.hlib.error response.error, () ->
      field.unmark_error()

  # Unauthorized - wrong password, ACL violations, ...
  s401:       (response, form) ->
    window.hlib.error response.error

  # Conflicting errors - impossible requests, joining already joined games, etc...
  s402:       (response, form) ->
    window.hlib.error response.error

  # Invalid (not malformed!) input - duplicit names, unknown names etc.
  s403:       (response, form) ->
    field = form.invalid_field(response)
    field.mark_error()

    window.hlib.error response.error, () ->
      field.unmark_error()

  # Internal server error
  s500:		(response, form) ->
    window.hlib.error response.error

window.hlib.ajax_default_handlers =
  # Redirect
  h303:		(response, form) ->
    window.hlib.redirect response.redirect.url

  # Internal server error
  h500:		(response, form) ->
    window.hlib.error response.error

window.hlib.setup_common = (opts) ->
  window.hlib.OPTS = opts
  window.hlib.INFO = new window.hlib.Info
