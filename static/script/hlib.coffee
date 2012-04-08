String.prototype.format = () ->
  args = arguments;
  return @replace /\{(\d+)\}/g, (m, n) -> return args[n]

window.hlib =
  templates:	{
  }

  OPTS:		null
  INFO:		null

  _g:		(s) ->
    return s

  disable:	(fid) ->
    if not $('#' + fid).hasClass 'disabled'
      $('#' + fid).addClass 'disabled'

  enable:	(fid) ->
    $('#' + fid).removeClass 'disabled'

  enableIcon:	(sel, callback) ->
    $(sel).removeClass 'icon-disabled'
    $(sel).click () ->
      callback()
      return false

  disableIcon:	(sel) ->
    $(sel).removeClass 'icon-disabled'
    $(sel).addClass 'icon-disabled'
    $(sel).click () ->
      return false

  dump:	(arr, level) ->
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

  clone:	(obj) ->
    if not obj? or typeof obj isnt 'object'
      return obj

    newInstance = new obj.constructor()

    for key of obj
      newInstance[key] = clone obj[key]

    return newInstance

  redirect:	(url) ->
    window.location.replace url

  setTitle:	(msg) ->
    document.title = msg

  __set_row_number:	(oSettings, i) ->
    $('td:eq(0)', oSettings.aoData[oSettings.aiDisplay[i]].nTr).html oSettings._iDisplayStart + i + 1

  recalc_row_numbers:	(oSettings) ->
    window.hlib.__set_row_number oSettings, i for i in [0..oSettings.aiDisplay.length - 1]

  render:		(tmpl, data) ->
    Mustache.to_html(tmpl, data)

  form_default_handlers:
    # Everything is all right
    s200:	(response, form) ->
      if response.form_info.hasOwnProperty 'updated_fields'
        form.update_fields response.form_info.updated_fields

      form.info.success 'Successfully changed'

    # Bad Request - empty fields, invalid values, typos, ...
    s400:       (response, form) ->
      field = form.invalid_field(response)
      field.mark_error()

      window.hlib.INFO.error response.message, () ->
        field.unmark_error()

    # Unauthorized - wrong password, ACL violations, ...
    s401:       (response, form) ->
      window.hlib.INFO.error response.message

    # Conflicting errors - impossible requests, joining already joined games, etc...
    s402:       (response, form) ->
      window.hlib.INFO.error response.message

    # Invalid (not malformed!) input - duplicit names, unknown names etc.
    s403:       (response, form) ->
      field = form.invalid_field()
      field.mark_error()

      window.hlib.INFO.error response.message, () ->
        field.unmark_error()

  setup_common: (opts) ->
    window.hlib.OPTS = opts
    window.hlib.INFO = new window.hlib.Info

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

    $.ajax
      dataType:		'json'
      type:		'POST'
      url:		opts.url
      async:		opts.async
      data:		opts.data

      beforeSend:	() ->
        window.hlib.INFO.working()

      success:		(response) ->
        handler_name = 'h' + response.status

        if not opts.handlers.hasOwnProperty handler_name
          window.hlib.INFO.error 'Unknown success handler ' + handler_name
          return

        opts.handlers[handler_name] response, _ajax

      error:		(request, msg, e) ->
        window.hlib.INFO.error msg

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

  constructor: (opts) ->
    @fid = '#' + opts.fid + '_form'
    @base_fid = opts.fid
    @info = new FormInfo(@)

    if not opts.hasOwnProperty 'submit_empty'
      opts.submit_empty = false

    _form = @

    $(@fid).ajaxForm
      dataType:		'json'
      success:	(response) ->
        window.hlib.INFO._hide()
        $(_form.fid).clearForm()

        reply_handler = 's' + response.status

        if response.status != 200 and opts.hasOwnProperty('refill') and opts.refill and response.form_info.hasOwnProperty('orig_fields')
          $(_form.fid + '_' + key).val(value) for own key, value of response.form_info.orig_fields

        if opts.hasOwnProperty('handlers') and opts.handlers.hasOwnProperty(reply_handler)
          opts.handlers[reply_handler] response, _form
          return

        else
          if window.hlib.form_default_handlers.hasOwnProperty reply_handler
            window.hlib.form_default_handlers[reply_handler] response, _form
            return

        window.hlib.INFO.error response.form_info

      beforeSerialize:		(f, o) ->
        if opts.submit_empty != true
          f.find(':input[value=""]').attr 'disabled', 'disabled'

        return true

      beforeSubmit:             (a, f, o) ->
        if opts.submit_empty != true
          f.find(':input[value=""]').attr 'disabled', ''

        window.hlib.INFO.working()
        return true

    if not opts.hasOwnProperty('dont_clean') or opts.dont_clean != true
      $(@fid).clearForm()

    if opts.hasOwnProperty 'focus'
      $('#' + @base_fid + '_' + opts.focus).focus()

  field_id:		(name) ->
    '#' + @base_fid + '_' + name

  invalid_field:	(response) ->
    if not response.form_info.hasOwnProperty 'invalid_field'
      return null

    new FormField @.field_id response.form_info.invalid_field

  update_fields:	(fields) ->
    _form = @
    __update_field = (f, v) ->
      $(_form.field_id f).val v

    __update_field f, v for f, v of fields
