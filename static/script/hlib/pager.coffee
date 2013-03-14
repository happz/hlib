window.hlib ?= {}

class window.hlib.Pager
  constructor: (opts) ->
    default_options =
      after_refresh: (response, pager) ->
        return

    @opts = $.extend true, {}, default_options, opts

    _pager = @

    @start	= opts.start
    @length	= opts.length
    @items	= null

    $(@opts.eid + ' .' + @opts.id_prefix + '-first').click () ->
      _pager.first()
      return false

    $(@opts.eid + ' .' + @opts.id_prefix + '-last').click () ->
      _pager.last()
      return false

    $(@opts.eid + ' .' + @opts.id_prefix + '-prev').click () ->
      _pager.prev()
      return false

    $(@opts.eid + ' .' + @opts.id_prefix + '-next').click () ->
      _pager.next()
      return false

  refresh: () ->
    _pager = @

    data =
      start:		_pager.start
      length:		_pager.length

    $.extend data, _pager.opts.data

    new window.hlib.Ajax
      url:		_pager.opts.url
      data:		data
      handlers:
        h200: (response, _ajax) ->
          _pager.items = response.page.cnt_total

          $(_pager.opts.eid + ' tbody').html ''
          $(_pager.opts.eid + ' tbody').append _pager.opts.template record for record in response.page.records

          $(_pager.opts.eid + ' .' + _pager.opts.id_prefix + '-position').html '' + (_pager.start + 1) + '. - ' + (Math.min _pager.items, _pager.start + response.page.cnt_display) + '. z ' + _pager.items

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

