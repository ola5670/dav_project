# COVID-19 in Germany

Student project for the Data Analysis and Visualization course, University of Warsaw, 2026.

The project analyzes the COVID-19 pandemic in Germany. Poland is included as comparison-ready processed data for later parts of the project.

## Current Status

Done:

- data download/preparation based on the Our World in Data COVID-19 dataset,
- cleaned Germany dataset and Germany-Poland comparison dataset,
- five reproducible static plots.

Still to do:

- HTML presentation,
- interactive and/or animated plots,
- inferential statistics and trend prediction,
- extended comparison with Poland,
- final cleanup before submission.

## Data

Main source used in the current analysis:
- Our World in Data COVID-19 dataset: <https://raw.githubusercontent.com/owid/covid-19-data/refs/heads/master/public/data/owid-covid-data.csv>
- OWID codebook: <https://raw.githubusercontent.com/owid/covid-19-data/refs/heads/master/public/data/owid-covid-codebook.csv>

In the downloaded OWID file, Germany daily case/death reporting is available through **15 July 2023**, while cumulative totals continue through **4 August 2024**.

Raw data are stored in `data/raw/`. Processed data used by the plots are stored in `data/processed/`. The cleaning script `scripts/01_clean_merge.py` filters the main OWID dataset to Germany (`DEU`) and Poland (`POL`).

Additional raw files, not used in the current plots:
- `owid_weekly_cases_current.csv`: OWID Grapher weekly cases dataset, <https://ourworldindata.org/grapher/weekly-covid-cases.csv>
- `owid_weekly_deaths_current.csv`: OWID Grapher weekly deaths dataset, <https://ourworldindata.org/grapher/weekly-covid-deaths.csv>
- `ecdc_variants.csv`: ECDC SARS-CoV-2 variants dataset, <https://www.ecdc.europa.eu/en/publications-data/data-virus-variants-covid-19-eueea>

## How To Run

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/run_part1.py
```

This regenerates the processed data and static plots.

## Project Structure

```text
covid19_Germany/
├── data/
│   ├── raw/          # source data
│   └── processed/    # cleaned data used for plots
├── output/
│   ├── figures/      # generated plots
│   └── poster.pdf    # current A0 poster
├── scripts/          # data cleaning and plotting scripts
├── build_poster.py   # poster generator
├── README.md
└── requirements.txt
```

## Reproducible Plots

Current static plots:

1. Daily cases and deaths in Germany.
2. 7-day incidence per 100,000 people.
3. Case fatality ratio over time.
4. Vaccination progress.
5. Incidence distribution by pandemic phase.

Each plot has a corresponding Python script in `scripts/`.

## Notes

- Negative daily case/death corrections are clipped only for rolling incidence and summary plots.
- CFR is descriptive and is not the same as infection fatality rate.
- Pandemic phases used in plots are fixed analysis periods, not official German definitions.
