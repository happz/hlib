ROOT_DIR="/data/settlers/hlib/"

DOC_DIR="$ROOT_DIR/doc/"
CONF_DIR="$ROOT_DIR/conf/"

PACKAGES=". events handlers http log templates ui"

EPYDOC_OPTIONS="--config $CONF_DIR/makedoc.conf -c static/css/epydoc.css"
PYLINT_OPTIONS="--rcfile=$CONF_DIR/pylintrc -r no"
