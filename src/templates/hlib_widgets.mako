<%!
  import hruntime
%>

<%def name="w_helper_id(i, default = None)">
  <%
    if i == None:
      if default:
        return 'id="%s"' % default

      return ''

    return 'id="%s"' % i
  %>
</%def>

<%def name="w_helper_class(cls, append = None)">
  <%
    append = append or []
    cls = cls or []

    cls += append
    return 'class="%s"' % ' '.join(cls)
  %>
</%def>

<%def name="w_helper_style(styles, append = None)">
  <%
    append = append or []
    styles = styles or []

    styles += append
    return 'style="%s"' % '; '.join(styles)
  %>
</%def>

<%def name="w_helper_selected(s)">
  <%
    if s == True:
      return 'selected="selected"'
    return ''
  %>
</%def>

<%def name="w_helper_label(label, required = False, append_colon = True)">
  <label>
  <%
    _label = label
    if append_colon == True:
      _label += ':'
  %>
  ${_(_label)}
  % if required == True:
    <em class="formee-req">*</em>
  % endif
  </label>
</%def>

<%def name="w_form_start(action, legend, id, method = None, classes = None, not_working = False)">
  <%
    method = method or 'post'

    hruntime.ui_form = id
  %>

  <form action="${action}" method="${method}" ${w_helper_class(classes, append = ['formee'])} id="${id}_form">
    <fieldset>
      <legend>${_(legend)}</legend>
      <div class="form-forminfo"></div>
      % if not_working:
        <div class="formee-msg-error"><label>${_('This form is not working yet.')}</label></div>
      % endif
</%def>

<%def name="w_form_input(name, type, label = None, required = False, append_colon = False, default = None, struct = True)">
  % if struct == True:
    <div class="grid-12-12">
  % endif
  % if label != None:
    ${w_helper_label(label, required = required, append_colon = append_colon)}
  % endif
  <%
    default = default or ''
  %>
  <input type="${type}" name="${name}" id="${hruntime.ui_form + '_' + name}" value="${default}" />
  % if struct == True:
    </div>
  % endif
</%def>

<%def name="w_form_select(name, label = None, default = True, required = False, struct = True)">
  % if struct == True:
    <div class="grid-12-12">
  % endif
  % if label != None:
    ${w_helper_label(label, required = required)}
  % endif
  <select name="${name}" id="${hruntime.ui_form + '_' + name}">

  % if default == True:
    <option value="" selected="selected">${_('Choose...')}</option>
  % endif
</%def>

<%def name="w_form_text(name, label = None, rows = 7, cols = 90, default = None, struct = True)">
  % if struct:
    <div class="grid-12-12">
  % endif

  % if label != None:
    ${w_helper_label(label, required = False, append_colon = False)}
  % endif
  <%
    default = default or ''
  %>
  <textarea name="${name}" id="${hruntime.ui_form + '_' + name}" rows="${rows}" cols="${cols}">${default}</textarea>
  % if struct:
    </div>
  % endif
</%def>

<%def name="w_form_end()">
    </fieldset>
  </form>
  <%
    hruntime.ui_form = None
  %>
</%def>

<%def name="w_form_label(label, required = False, append_colon = True)">
  ${w_helper_label(label, required = required, append_colon = append_colon)}
</%def>

<%def name="w_option(value, selected, label, classes = None, style = None)">
  <option ${w_helper_selected(selected)} value="${value}" ${w_helper_class(classes)} ${w_helper_style(style)}>${label}</option>
</%def>

<%def name="w_submit_button(label, id = None)">
  <input class="right" type="submit" title="${_(label)}" value="${_(label)}" ${w_helper_id(id)} />
</%def>

<%def name="w_submit_row(label, classes = None)">
  <div ${w_helper_class(classes, append = ['grid-12-12'])}>
    ${w_submit_button(label)}
  </div>
</%def>
