all:
	trash Generated
	python insert_imports.ppy
	cd Render && python render.py && python unify.py
	@echo "\nRunning main.py statically..." && python main.py && echo "Done. ✅\n"

