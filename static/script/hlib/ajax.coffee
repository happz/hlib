window.hlib ?= {}

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

      statusCode:
        500: () ->
          window.hlib.error 'Server error', {message: 'Oh no! Server suddenly went away. Be sure we are all freaking out - take a break, get a coffee, and try again in 5 minutes or so.'}

      beforeSend:	() ->
        if _ajax.opts.show_spinner == true
          window.hlib.WORKING.show()

      complete:			(jqXHR, textStatus) ->
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
        response = $.parseJSON jqXHR.responseText
        _ajax.opts.handlers.error _ajax, response, jqXHR, textStatus

