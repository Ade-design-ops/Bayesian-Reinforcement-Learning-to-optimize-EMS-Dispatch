import numpy as np
import geopandas as gpd

##### Incidents Generation
# AI generated function: generated incidents given a population map, rate per hour per 1000 residents, and number of days


def generate_incidents(
    population_gdf,
    n_days,
    rate_per_1000_per_day=5.0,
    population_column="POP20",
    random_seed=None,
):
    """
    Generate N simulated days of incidents.

    Parameters
    ----------
    population_gdf : GeoDataFrame
        Census blocks with population and polygon geometry.

    n_days : int
        Number of days to simulate.

    rate_per_1000_per_day : float
        Expected incidents per 1,000 residents per day.

    population_column : str
        Population field, normally "POP20".

    random_seed : int or None
        Seed for reproducibility.

    Returns
    -------
    GeoDataFrame
        One row per incident.

        Columns:
            incident_id
            day
            seconds_since_midnight
            hour
            minute
            second
            block_index
            population
            expected_incidents
            latitude
            longitude
            geometry
    """

    if n_days < 1:
        raise ValueError("n_days must be at least 1")

    rng = np.random.default_rng(random_seed)

    blocks = population_gdf.copy()

    # Keep only populated blocks with valid geometry
    blocks = blocks[
        blocks[population_column].notna()
        & (blocks[population_column] > 0)
        & blocks.geometry.notna()
    ].copy()

    # Expected incidents per block per day
    blocks["expected_incidents"] = (
        blocks[population_column]
        * rate_per_1000_per_day
        / 1000.0
    )

    # Representative point for each block
    blocks_wgs84 = blocks.to_crs("EPSG:4326")
    blocks_wgs84["representative_point"] = (
        blocks_wgs84.geometry.representative_point()
    )

    incident_records = []
    incident_id = 0

    for day in range(n_days):

        # Draw number of incidents independently for every block
        n_incidents = rng.poisson(
            blocks_wgs84["expected_incidents"].to_numpy()
        )

        for (block_index, block), n in zip(
            blocks_wgs84.iterrows(),
            n_incidents,
        ):

            n = int(n)

            if n == 0:
                continue

            point = block["representative_point"]

            latitude = point.y
            longitude = point.x

            # Generate all occurrence times for this block
            seconds = rng.uniform(
                0,
                24 * 60 * 60,
                size=n,
            )

            for seconds_since_midnight in seconds:

                total_seconds = int(seconds_since_midnight)

                hour = total_seconds // 3600
                minute = (total_seconds % 3600) // 60
                second = total_seconds % 60

                incident_records.append(
                    {
                        "day": day,
                        "seconds_since_midnight": seconds_since_midnight,
                        "hour": hour,
                        "minute": minute,
                        "second": second,
                        "block_index": block_index,
                        "latitude": latitude,
                        "longitude": longitude,
                        "geometry": point,
                    }
                )

                incident_id += 1

    incidents = gpd.GeoDataFrame(
        incident_records,
        geometry="geometry",
        crs="EPSG:4326",
    )

    # Put incidents in chronological simulation order
    incidents = (
        incidents
        .sort_values(
            ["day", "seconds_since_midnight"]
        )
        .reset_index(drop=True)
    )

    return incidents