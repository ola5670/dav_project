# COVID-19 in Germany

Project analyzes the COVID-19 pandemic in Germany using descriptive statistics, inferential methods, short-term trend prediction, vaccination data, excess mortality, variant surveillance and comparison with Poland.

## Final Outputs

- PDF poster: `output/poster.pdf`
- HTML presentation: `output/presentation.html`
- Generated figures: `output/figures/`
- Raw datasets: `data/raw/`
- Processed datasets used by plots: `data/processed/`
- Data cleaning and plot scripts: `scripts/`

## Data Sources

- Our World in Data COVID-19 dataset: <https://raw.githubusercontent.com/owid/covid-19-data/refs/heads/master/public/data/owid-covid-data.csv>
- OWID COVID-19 codebook: <https://raw.githubusercontent.com/owid/covid-19-data/refs/heads/master/public/data/owid-covid-codebook.csv>
- ECDC SARS-CoV-2 variants dataset: <https://www.ecdc.europa.eu/en/publications-data/data-virus-variants-covid-19-eueea>

The main cleaning script, `scripts/01_clean_merge.py`, prepares Germany data and Germany-Poland comparison data. In the OWID file used here, Germany daily case/death reporting is available through 9 July 2023, while cumulative totals continue through 4 August 2024.

## Plots and Analyses

The project contains ten reproducible plots:

1. Daily COVID-19 cases and deaths in Germany.
2. 7-day incidence per 100,000 people.
3. Case fatality ratio over time.
4. Vaccination progress.
5. Incidence distribution by pandemic phase.
6. Log-linear regression of epidemic growth and doubling time.
7. Short-term forecast using Holt-Winters exponential smoothing.
8. Germany vs Poland comparison.
9. Excess mortality in Germany.
10. SARS-CoV-2 variant dominance in Germany.

Selected analyses also generate interactive or animated Plotly files in `output/figures/`.

## Methodology Notes

The analysis uses 7-day rolling averages and rates per 100,000 people to reduce weekday reporting effects and make periods or countries easier to compare.

Negative daily corrections in cases or deaths are clipped only where needed for rolling-rate calculations and summary plots. The case fatality ratio is descriptive and should not be interpreted as infection fatality rate.

Pandemic phases are fixed analysis periods used for visualization and comparison. They are not official German epidemiological definitions.

The regression analysis estimates exponential growth during selected wave-growth periods. The forecast uses Holt-Winters exponential smoothing for short-term prediction and includes prediction intervals.

## How To Reproduce

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 scripts/run_part1.py
python3 scripts/run_part2.py
python3 build_poster.py
python3 build_presentation.py
```

This regenerates the processed datasets, all figures, the PDF poster and the HTML presentation.


