# make        rebuild numbers, figure and PDF from bench/results/
# make pdf    PDF only
all: data pdf

data:
	cd ../bench && python3 export_tex.py
	python3 make_figs.py

pdf:
	tectonic main.tex

.PHONY: all data pdf
