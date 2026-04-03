all:
	python insert_imports.ppy
	trash Generated  # keep this!
	cd Render && python render.py && python unify.py
	@echo "\nRunning main.py statically..." && python main.py && echo "Done. ✅\n"

