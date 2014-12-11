
lint:
	find -iname '*.py' | grep -E -v -f no_linting.grep | sort | xargs cienv/bin/pylint --output-format=colorized --reports=n --disable=C,R,I0011,W0142,W0603,W0223,W0511,W0123 --msg-template='{line}: {msg}({msg_id})'
	
lint-suggest:
	find -iname '*.py' | grep -E -v -f no_linting.grep | sort | xargs cienv/bin/pylint --output-format=colorized --reports=n  --disable=C,W,E,I --enable=R,W0603 --msg-template='{line}: {msg}({msg_id})' 
	
test:
	cienv/bin/nosetests --with-process-isolation --processes=8 --process-timeout=120

cover:
	cienv/bin/nosetests --with-coverage --cover-inclusive --cover-erase --cover-package=voldemort

setup:
	rm -rf cienv
	virtualenv --system-site-packages cienv
	cienv/bin/pip install -I -r requirements.txt
	gradle shadowJar
	mv build/libs/*.jar jvoldemort/voldemort-python.jar

setup-dev: setup
	cienv/bin/pip install -I -r dev-requirements.txt

clean:
	find -iname '*.pyc' -delete 
	rm -f *~
	rm -rf cover*
	rm -f nosetests.xml
	rm -rf build
	rm -rf dist
	rm -rf *egg-info*
	
all: clean setup-dev lint test

test-ci: clean setup-dev
	cienv/bin/python cienv/bin/nosetests --with-process-isolation --processes=8 --process-timeout=240
	find -iname '*.py' | grep -E -v -f no_linting.grep | sort | xargs cienv/bin/pylint --output-format=colorized --reports=n --disable=C,R,I0011,W0142,W0603,W0223,W0511,W0123 --msg-template='{line}: {msg}({msg_id})' 

