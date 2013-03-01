ROOT_DIR=$(CURDIR)

CONF_DIR := $(ROOT_DIR)/conf/
DOC_DIR := $(ROOT_DIR)/doc/
SRC_DIR=$(ROOT_DIR)/src/
SCRIPT_DIR := $(ROOT_DIR)/static/script

CLOC_OPTIONS := --read-lang-def=$(CONF_DIR)/cloc.langs --exclude-dir=$(ROOT_DIR)/compiled/ --exclude-ext=js,css --skip-uniqueness $(SRC_DIR) $(ROOT_DIR)/static/script/ $(ROOT_DIR)/static/css/

EPYDOC_OPTIONS := --config $(CONF_DIR)/makedoc.conf -c static/css/epydoc.css

PYLINT_OPTIONS := --rcfile=$(CONF_DIR)/pylintrc -r no
PYLINT_PACKAGES := events handlers http log ui

.PHONY: clean cloc doc pylint tests test_all

clean:
	@rm -f `find $(ROOT_DIR) -name '*~'`

cloc:
	@echo "----- ----- ----- ----- ----- ----- ----- ----- -----"
	@echo "Cloc status"
	@cloc $(CLOC_OPTIONS)
	@echo "----- ----- ----- ----- ----- ----- ----- ----- -----"

doc:
	@echo "----- ----- ----- ----- ----- ----- ----- ----- -----"
	@echo "Documentation"
	@rm -rf $(DOC_DIR)
	@epydoc -v -o $(DOC_DIR) $(EPYDOC_OPTIONS) hlib
	@echo "----- ----- ----- ----- ----- ----- ----- ----- -----"

doccheck:
	@echo "----- ----- ----- ----- ----- ----- ----- ----- -----"
	@echo "Documentation check"
	@epydoc -v --check hlib
	@echo "----- ----- ----- ----- ----- ----- ----- ----- -----"

pylint:
	@echo "----- ----- ----- ----- ----- ----- ----- ----- -----"
	@echo "Pylint checks"
	@echo
	@PYTHONPATH=$(SRC_DIR)/ pylint $(PYLINT_OPTIONS) $(PYLINT_PACKAGES) 2> /dev/null | grep -v 'Locally disabling'
	@echo "----- ----- ----- ----- ----- ----- ----- ----- -----"

coffeelint:
	@echo "----- ----- ----- ----- ----- ----- ----- ----- -----"
	@echo "CoffeeLint checks"
	@echo
	@coffeelint -f $(CONF_DIR)/coffeelint.json --nocolor `find $(SCRIPT_DIR) -name '*.coffee'`
	@echo "----- ----- ----- ----- ----- ----- ----- ----- -----"

tests:
	@echo "----- ----- ----- ----- ----- ----- ----- ----- -----"
	@echo "Nose tests"
	@echo
	@nosetests $(NOSE_OPTIONS)
	@echo "----- ----- ----- ----- ----- ----- ----- ----- -----"

test_all: pylint coffeelint tests

checksupdate: pylint coffeelint tests doccheck doc cloc
