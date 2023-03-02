install: 
	pip3 install pylint
lint:
	find . -type f -name "*.py" | xargs pylint --rcfile=.pylintrc
test:
	python3 -m unittest
performance:
	python3 -m unittest tests.performance.TestPerformance
performance2:
	python3 -m unittest tests.large_op_performance.TestLargeOpPerformance
clean:
	rm -rf __pycache__