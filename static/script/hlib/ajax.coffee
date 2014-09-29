window.hlib ?= {}

class window.hlib.AjaxV2
  constructor: (opts) ->
    _ajax = @

    __submit_error = (error_msg, ajax, response, xhr) ->
      window.hlib.submit_error
        error_msg:   error_msg
        text_status: jqXHR.statusText
        response:    response
        url:         ajax.opts.url
        data:        ajax.opts.data

    _default_opts =
      method:    'GET'
      url:       null
      async:     true
      data:      null
      user:      null
      password:  null
      timeout:   20000

      # UI options
      keep_focus: false
      focused_element: null
      show_spinner: true

      # Handlers
      handlers:
        # Redirect
        h303: (response, ajax) ->
          window.hlib.redirect response.redirect.url

        # Invalid (not malformed!) input - duplicit names, unknown names etc.
        h403: (response, ajax) ->
          window.hlib.error '', response.error

        # Internal server error
        h500: (response, ajax) ->
          window.hlib.error 'Internal error', response.error

        # Error
        error: (ajax, response, xhr) ->
          __submit_error 'AJAX failed', ajax, response, xhr

    @opts = $.extend true, {}, default_opts, opts

    @xhr = _xhr = new XMLHttpRequest()
    @xhr.responseType = 'json'
    @xhr.open @opts.method, @opts.url, @opts.async, @opts.user, @opts.password

    @xhr.onreadystatechange = () ->
      if @readyState != 4
        return

      if @status == 500
        window.hlib.WORKING.hide()
        window.hlib.server_offline()
        return

      response = JSON.parse _xhr.responseText

      if @status < 200 or @status >= 400
        _ajax.opts.handlers.error _ajax, response, _xhr, _xhr.statusText
        return

      handler_name = 'h' + response.status
      if not _ajax.opts.handlers.hasOwnProperty handler_name
        __submit_error 'No handler for response status', _ajax, response, _xhr
        return

      handler = _ajax.opts.handlers[handler_name]
      handler response, _ajax

      if _ajax.opts.keep_focus and _ajax.opts.focused_element
        _ajax.opts.focused_element.focus()

  open: () ->
    form_data = null

    if @method == 'POST'
      form_data = new FormData()
      @xhr.setRequestHeader 'Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8'

      if @opts.data
        form_data.append(key, JSON.stringify(@opts.data[key])) for key of @opts.data

    if @opts.keep_focus
      @opts.focused_element = document.activeElement

    if @opts.show_spinner
      window.hlib.WORKING.show()

    @xhr.send form_data
    @xhr = null

class window.hlib.Ajax
  constructor:		(opts) ->
    _ajax = @

    default_options =
      method:         'POST'
      timeout:        20000
      data:           {}
      keep_focus:     false
      show_spinner:   true
      handlers:
        # Redirect
        h303:         (response, ajax) ->
          window.hlib.redirect response.redirect.url

        # Invalid (not malformed!) input - duplicit names, unknown names etc.
        h403:         (response, ajax) ->
          window.hlib.error '', response.error

        # Internal server error
        h500:         (response, ajax) ->
          window.hlib.error 'Internal error', response.error

        # Error
        error:        (ajax, response, jqXHR, textStatus) ->
          window.hlib.submit_error
            error_msg:              'AJAX failed'
            text_status:            textStatus
            response:               response
            url:                    ajax.opts.url
            data:                   ajax.opts.data
            jqXHR:                  jqXHR

    @opts = $.extend true, {}, default_options, opts

    focus_elements = $(document.activeElement)

    $.ajax
      dataType:     'json'
      type:         _ajax.opts.method
      url:          _ajax.opts.url
      data:         _ajax.opts.data
      cache:        false
      timeout:      _ajax.opts.timeout
      async:        true

      beforeSend:	() ->
        if _ajax.opts.show_spinner == true
          window.hlib.WORKING.show()

      complete:			(jqXHR, textStatus) ->
        if jqXHR.status == 500
          window.hlib.WORKING.hide()
          window.hlib.server_offline()
          return

        response = $.parseJSON jqXHR.responseText

        if textStatus != 'success'
          _ajax.opts.handlers.error _ajax, response, jqXHR, textStatus
          return

        handler_name = 'h' + response.status
        if not _ajax.opts.handlers.hasOwnProperty handler_name
          window.hlib.submit_error
            error_msg:          'No handler for response status'
            response:           response
            opts:               _ajax.opts
            url:                _ajax.opts.url

          return

        handler = _ajax.opts.handlers[handler_name]
        handler response, _ajax

        if _ajax.opts.keep_focus and focus_elements[0] and focus_elements[0].id
          $('#' + focus_elements[0].id).focus()

      error:			(jqXHR, textStatus, errorThrown) ->
        if jqXHR.status == 500
          window.hlib.WORKING.hide()
          window.hlib.server_offline()
          return

        response = $.parseJSON jqXHR.responseText
        _ajax.opts.handlers.error _ajax, response, jqXHR, textStatus

