<%!
  import types
  import sys
  import hlib.i18n

  import hruntime
%>

<%def name="quote(s)">${'"' + s + '"'}</%def>

<%def name="script_file(file, type)">
  <%
    if type == 'js':
      type = 'text/javascript'
      ext = 'js'

    elif type == 'coffee':
      type = 'text/coffeescript'
      ext = 'coffee'
  %>
  <script type="${type}" src="/static/script/${file}.${ext}"></script>
</%def>

<%def name="stylesheet(file)">
  <link rel="stylesheet" type="text/css" href="/static/css/${path}" />
</%def>

##
## Inheritance methods
##
<%def name="page_title()">
</%def>

<%def name="page_favicon()">
  <link rel="shortcut icon" href="http://${basepath}/static/images/favicon.gif" type="image/gif" />
  <link rel="icon" href="http://${basepath}/static/images/favicon.gif" type="image/gif" />
</%def>

<%def name="page_style()">
</%def>

<%def name="page_script()">
</%def>

<%def name="page_header()">
  <title>${self.page_title()}</title>

  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />

  ${self.page_favicon()}

  <style type="text/css">
    ${self.page_style()}
  </style>

  <script type="text/coffeescript">
    ${self.page_script()}
  </script>

  <script type="text/coffeescript">
    $(document).ready ->
      window.hlib.startup()
  </script>
</%def>

<%def name="page_pre_body()">
</%def>

<%def name="page_post_body()">
</%def>

<%def name="page_footer()">
</%def>


<!DOCTYPE html>
<html>
  <head>
    ${self.page_header()}
  </head>

  <body>
    ${self.page_pre_body()}

    ${next.body()}

    ${self.page_post_body()}
  </body>
</html>
