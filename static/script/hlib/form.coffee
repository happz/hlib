window.hlib ?= {}

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

class window.hlib.FormInfo
  constructor: (@form) ->
    @eid = @form.fid + ' .form-info'

  _show: (msg, title, cls) ->
    $(@eid + ' strong').html ''
    $(@eid).removeClass 'alert-error'
    $(@eid).removeClass 'alert-success'

    $(@form.fid + ' p').html msg

    $(@eid + ' strong').html ''
    if title
      $(@eid + ' strong').html title

    if cls
      $(@eid).addClass cls

    $(@eid).show()

  _hide: () ->
    $(@eid).hide()

  error: (msg) ->
    @_show msg, (window.hlib._g 'Error!'), 'alert-error'

  success: (msg, dont_fade) ->
    @_show msg, '', 'alert-success'

    if dont_fade
      return

    $(@eid).fadeOut 3000

class window.hlib.Form
  clear: () ->
    $(@field_id name).val '' for name in @opts.clear_fields

  constructor: (opts) ->
    @default_options =
      fid:              null
      timeout:          10000
      focus:            null
      clear_fields:     []
      disable_fields:   []
      submit_empty:     false
      refill:           false
      validate:         null
      validators:       {}
      validator:        null
      handlers:
        # Everything is all right
        h200: (response, form) ->
          if response.hasOwnProperty('form') and response.form and response.form.hasOwnProperty 'updated_fields'
            form.update_fields response.form.updated_fields

          form.info.success 'Successfully changed'

        # Redirect
        h303: (response, form) ->
          window.hlib.redirect response.redirect.url

        # Bad Request - empty fields, invalid values, typos, ...
        h400:				(response, form) ->
          form.invalid_field(response).mark_error()
          form.info.error window.hlib.format_error response.error

        # Unauthorized - wrong password, ACL violations, ...
        h401:       (response, form) ->
          window.hlib.error 'Unauthorized', response.error

        # Conflicting errors - impossible requests, joining already joined games, etc...
        h402:       (response, form) ->
          window.hlib.error 'Conflict error', response.error

        # Invalid (not malformed!) input - duplicit names, unknown names etc.
        h403:       (response, form) ->
          form.invalid_field(response).mark_error()
          form.info.error window.hlib.format_error response.error

        # Internal server error
        h500:		(response, form) ->
          window.hlib.error 'Internal error', response.error

        # Called after all handlers
        after: (response, form) ->
          return

    _form = @

    @opts = $.extend true, {}, @default_options, opts

    @fid = '#' + @opts.fid + '_form'
    @info = new window.hlib.FormInfo(@)
    @fields = {}
    @last_invalid_field = null

    if not @opts.validate
      @opts.validate = ($(@fid).attr('data-validate') == 'true')

    @form_opts =
      dataType:		'json'
      timeout:		@opts.timeout
      success: (response) ->
        window.hlib.MESSAGE.hide()

        _form.clear()

        if response.status != 200 and _form.opts.refill == true and response.form.hasOwnProperty('orig_fields')
          $(_form.field_id key).val value for own key, value of response.form.orig_fields

        handler_name = 's' + response.status
        if not _form.opts.handlers.hasOwnProperty(handler_name)
          handler_name = 'h' + response.status
          if not _form.opts.handlers.hasOwnProperty(handler_name)
            return window.hlib.submit_error
              error_msg:          'No handler for response status'
              response:           response
              opts:               _form.opts

        handler = _form.opts.handlers[handler_name]
        handler response, _form

        _form.opts.handlers.after response, _form

      beforeSerialize: (f, o) ->
        if _form.opts.submit_empty != true
          f.find(':input[value=""]').attr 'disabled', 'disabled'

        return true

      beforeSubmit:             (a, f, o) ->
        f.find(':input[value=""]').removeAttr 'disabled'

        _form.info._hide()
        if _form.last_invalid_field
          _form.last_invalid_field.unmark_error()

        if _form.opts.validate
          if _form.opts.validate
            $(_form.fid).parsley
              showErrors: false
              successClass:		null
              errorClass:		null
              errors:
                errorsWrapper:		null
                errorElem:		null
              validators: _form.opts.validators
              listeners:
                onFieldValidate:	(elem) ->
                  return not $(elem).is(':visible')

                onFieldError:		(element, constraints, parsley_field) ->
                  if _form.last_invalid_field
                    return

                  _form.last_invalid_field = _form.field($(element).attr 'name').mark_error()

                  if parsley_field.options.errorMessage
                    _form.info.error window.hlib._g parsley_field.options.errorMessage

            $(_form.fid).parsley 'validate'
            $(_form.fid).parsley 'destroy'

          if _form.last_invalid_field
            return false

        window.hlib.WORKING.show()
        return true

    $(@fid).on 'submit', (event) ->
      event.preventDefault()

      $(_form.fid).ajaxSubmit _form.form_opts

      return false

    @clear()

    if @opts.focus
      $(@field_id _form.opts.focus).focus()

    (@field f).disable() for f in @opts.disable_fields

  submit:		() ->
    $(@fid).ajaxSubmit @form_opts

  field_id:		(name) ->
    '#' + @opts.fid + '_' + name

  field:		(name) ->
    if not @fields.hasOwnProperty(name)
      @fields[name] = new window.hlib.FormField (@field_id name), @

    return @fields[name]

  invalid_field:	(response) ->
    if not response.hasOwnProperty('form') or not response.form or not response.form.hasOwnProperty('invalid_field')
      return null

    return @field response.form.invalid_field

  update_fields:	(fields) ->
    $(@field_id f).val v for f, v of fields

