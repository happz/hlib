window.hlib ?= {}

#
# Methods
#
unless String::format
  String::format = () ->
    args = arguments
    return @replace /\{(\d+)\}/g, (m, n) -> return args[n]

unless String::capitalize
  String::capitalize = () ->
    return @charAt(0).toUpperCase() + this.slice 1

unless Array::filter
  Array::filter = (callback) ->
    element for element in this when callback(element)

window.hlib.OPTS		= null
window.hlib.MESSAGE		= null
window.hlib.INFO		= null
window.hlib.ERROR		= null
window.hlib.WORKING		= null

window.hlib.trace = () ->
  trace = printStackTrace()
  console.log trace.join '\n'

window.hlib._g = (s) ->
  if s.length <= 0
    return ''

  if not window.hlib.OPTS or not window.hlib.OPTS.i18n_table
    return s

  if window.hlib.OPTS and window.hlib.OPTS.i18n_table and window.hlib.OPTS.i18n_table.hasOwnProperty s
    return window.hlib.OPTS.i18n_table[s]

  error_data =
    error_msg: 'Unknown token'
    token:     s

  window.hlib.submit_error error_data, true

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
  if window.hlib.mobile == false
    $('a[rel=tooltip]').tooltip 'hide'
    $('button[rel=tooltip]').tooltip 'hide'

  $(sel).attr 'disabled', 'disabled'
  $(sel).unbind 'click'
  $(sel).click () ->
    return false

window.hlib.bind_tooltips = () ->
  $('a[rel=tooltip]').tooltip()
  $('button[rel=tooltip]').tooltip()

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

window.hlib.format_string = (str, params) ->
  __per_param = (name, value) ->
    str = str.replace '%(' + name + ')s', value

  __per_param name, value for own name, value of params
  return str

window.hlib.format_error = (error) ->
  return window.hlib.format_string (window.hlib._g error.message), error.params

window.hlib.error = (label, error, beforeClose) ->
  window.hlib.ERROR.show (window.hlib._g label), (window.hlib.format_error error), beforeClose

window.hlib.submit_error = (data, dont_show) ->
  data.page = window.location.href
  data.useragent = $.browser

  if not data.hasOwnProperty 'error_msg'
    data.error_msg = 'Unknown error'

  $.post '/submit_error', data, () ->

  if dont_show
    return

  window.hlib.error 'Unhandled error',
    message:    'Something unexpected has happened. Error report has been sent to server. Please, reload page using F5 key'
    params:     null

window.hlib.setup = (opts) ->
  window.onerror = (error_msg, file, line_number) ->
    window.hlib.submit_error
      error_msg:                error_msg
      file:                     file
      line_number:              line_number

  window.hlib.OPTS = opts

  window.hlib.MESSAGE = new window.hlib.MessageDialog opts.message_dialog
  window.hlib.INFO = new window.hlib.InfoDialog opts.message_dialog
  window.hlib.ERROR = new window.hlib.ErrorDialog opts.message_dialog
  window.hlib.WORKING = new window.hlib.WorkingDialog opts.message_dialog

  $(opts.message_dialog).modal
    show:			false

  window.hlib.mobile = false
  if $(opts.visibility_check_eid).css('display') == 'none'
    window.hlib.mobile = true
