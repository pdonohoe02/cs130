install: 
	pip3 install pylint
lint:
	find . -type f -name "*.py" | xargs pylint --rcfile=.pylintrc
test:
	python3 -m unittest
performance:
	python3 -m unittest tests.performance.TestPerformance
clean:
	rm -rf __pycache__