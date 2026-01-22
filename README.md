# Sustainable NFL Scheduling Model

The NFL leads all major U.S. sports leagues in terms of carbon footprint per game, primarily due to team travel. This project uses a Binary Integer Programming (BIP) model to generate an NFL season schedule that is most carbon-efficient with respect to travel.

The optimal NFL schedule for each year can be found in:

```text
model/output/<year>/<year>_schedule.csv
```

## Results

The chart below compares the total travel-related carbon emissions (in metric tonnes of CO₂) for the actual NFL schedules versus the optimal schedule produced by the model for every applicable year.

![Emissions Comparison](results/emissions_comparison_bar_metric_tonnes.png)


## Raw Data

<details>
<summary>Click to expand</summary>

| Year | Actual Schedule<br>(metric tonnes CO₂) | Optimal Schedule<br>(metric tonnes CO₂) | Percentage Decrease<br>(%) |
|------|------------------------------------|-------------------------------------|--------------------|
| 2021 | 10,421.56                          | 9,793.20                            | 6.03               |
| 2022 | 9,290.36                           | 8,823.58                            | 5.02               |
| 2023 | 10,572.54                          | 10,036.19                           | 5.07               |
| 2024 | 10,409.79                          | 9,845.80                            | 5.42               |
| 2025 | 10,294.44                          | 9,706.58                            | 5.71               |

</details>

## How it Works

1. NFL season matchups are determined by a rotating schedule of cross-division opponents combined with each team’s in-division ranking from the previous season. Playwright was used to scrape the official NFL website to obtain these divisional rankings. An algorithm then applied the NFL’s scheduling rules to generate the complete set of matchups for the season.

2. To estimate travel distances, Nominatim was used to geocode each team’s primary locations, including their headquarters, home stadium, and nearest major airport. Road travel distances were computed using Project OSRM, while flight distances were calculated using the Haversine formula. These distances were then converted into estimated carbon emissions based on the mode of travel.

3. A Binary Integer Programming (BIP) model was formulated in PuLP and solved with CBC to generate a full 18-week schedule that minimizes total travel-related carbon emissions. The SportsBlaze API was used to retrieve the actual NFL season schedules. These real-world schedules were compared against the optimized schedule to evaluate the model and quantify carbon emission savings.


