run:
	cd Render && python insert_imports.ppy
	@if [ -d Generated ]; then rm -r Generated; fi
	cd Render && python render.py $(FLAGS) && python unify.py
	#@echo "\nRunning main.py statically..." && python main.py && echo "Done. ✅\n"

all: FLAGS=
all: run

prod: FLAGS=--prod
prod: run
