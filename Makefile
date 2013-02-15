ROOT_DIR=$(CURDIR)

CONF_DIR := $(ROOT_DIR)/conf/
DOC_DIR := $(ROOT_DIR)/doc/
SRC_DIR=$(ROOT_DIR)/src/

CLOC_OPTIONS := --read-lang-def=$(CONF_DIR)/cloc.langs --exclude-dir=$(ROOT_DIR)/compiled/ --exclude-ext=js,css --skip-uniqueness $(SRC_DIR) $(ROOT_DIR)/static/script/ $(ROOT_DIR)/static/css/

EPYDOC_OPTIONS := --config $(CONF_DIR)/makedoc.conf -c static/css/epydoc.css

PYLINT_OPTIONS := --rcfile=$(CONF_DIR)/pylintrc -r no
PYLINT_PACKAGES := events handlers http log ui

.PHONY: clean cloc doc pylint tests test_all

clean:
	@rm -f `find $(ROOT_DIR) -name '*~'`

cloc:
	@cloc $(CLOC_OPTIONS)

doc:
	rm -rf $(DOC_DIR)
	epydoc -v -o $(DOC_DIR) $(EPYDOC_OPTIONS) hlib

doccheck:
	epydoc -v --check hlib

pylint:
	@PYTHONPATH=$(SRC_DIR)/ pylint $(PYLINT_OPTIONS) $(PYLINT_PACKAGES) 2> /dev/null | grep -v 'Locally disabling'

tests:
	@nosetests $(NOSE_OPTIONS)

test_all: pylint tests doccheck
