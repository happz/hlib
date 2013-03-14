window.hlib ?= {}

class window.hlib.Tabs
  constructor:			(@eid) ->
    @current_tab = null

    $(@eid).tabs()

  render:			() ->
    if not @current_tab
      return true

    $('#' + @current_tab).trigger 'hlib_render'

  show_tab:			(handle, name, index) ->
    tid = '#' + name

    $(tid).trigger 'hlib_render'
    $(@eid).tabs 'select', index
    @current_tab = name

    if handle.attr 'location-hash'
      window.location.hash = handle.attr('location-hash')

  show_by_hash:			(default_name) ->
    _tabs = @
    done = false

    $(_tabs.eid + '>ul>li>a').each (index, element) ->
      handle = $(@)
      if handle.attr('location-hash') != window.location.hash
        return

      name = (handle.attr 'href').substring 1

      _tabs.show_tab handle, name, index
      done = true
      return false

    if not done
      @show default_name

    return

  show:				(name) ->
    _tabs = @

    tid = '#' + name

    $(_tabs.eid + '>ul>li>a').each (index, element) ->
      if $(@).attr('href') != tid
        return

      _tabs.show_tab $(@), name, index
      return false

    return
