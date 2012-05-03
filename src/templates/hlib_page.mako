<%!
  import types
  import sys
  import hlib.i18n

  import hruntime
%>

<%def name="quote(s)">${'"' + s + '"'}</%def>

<%def name="script_file(file, type)">
  <script type="text/javascript" src="/static/script/${file}.js"></script>
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

  <script type="text/javascript">
    $(document).ready(function() {
      $(window).trigger('hlib_prestartup');
      $(window).trigger('hlib_startup');
      $(window).trigger('hlib_poststartup');
    });
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
