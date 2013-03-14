window.hlib ?= {}

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
