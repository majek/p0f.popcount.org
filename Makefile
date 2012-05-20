
.PHONY: all
all: deps run

run:
	./venv/bin/python server.py

# Prerequisites

.PHONY: deps
deps: venv/.ok

venv:
	virtualenv venv

venv/.ok: requirements.txt venv
	./venv/bin/pip install -r requirements.txt
	touch venv/.ok

distclean::
	rm -rf venv


# Development
WAITON=*.py *.html
serve:
	@if [ -e .pidfile.pid ]; then			\
		kill `cat .pidfile.pid`;		\
		rm .pidfile.pid;			\
	fi

	@while [ 1 ]; do					\
		echo " [*] Running http server";		\
		make run &					\
		SRVPID=$$!;					\
		echo $$SRVPID > .pidfile.pid;			\
		echo " [*] Server pid: $$SRVPID";		\
		inotifywait -r -q -e modify $(WAITON);		\
		kill `cat .pidfile.pid`;			\
		rm -f .pidfile.pid;				\
		sleep 0.1;					\
	done


run_stunnel:
	sudo ~/src/stunnel-4.53/src/stunnel stunnel.conf

run_haproxy:
	sudo ~/src/haproxy-1.5-dev7/haproxy -f haproxy.cfg -d

run_p0f:
	-mv p0f.log p0f-`date +"%s"`.log
	sudo ../p0f/p0f -i any -f ../p0f/p0f.fp -o p0f.log "port 80 or port 443 or port 9999" 

run_parse_p0f:
	tail -F p0f.log | PYTHONPATH=. ./venv/bin/python website/parse_p0f.py
