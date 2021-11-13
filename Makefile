# Or ev3dev.local
ADR = 192.168.2.2

sr:
	make send run

send:
	scp -r ./*.py robot@$(ADR):res
	# ssh robot@ev3dev.local mkdir -p res/src
	# scp -r ./src/*.py robot@$(ADR):res/src

con:
	ssh robot@ev3dev.local # password: maker

id:
	ssh-copy-id robot@$(ADR)

run:
	ssh robot@$(ADR) python3 ./res/main.py
