from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import country_converter as coco


INPUT_FILE = Path("Faculty_and_participants.xlsx")
SHEET_NAME = "Sheet1"

AFFILIATION_COL = "Country of affiliation"
NATIONALITY_COL = "Nationality"

UNKNOWN_VALUES = {
    "",
    "not publicly confirmed",
    "unknown",
    "n/a",
    "na",
    "none",
}

COUNTRY_FIXES = {
    # Fix typo in the curated spreadsheet
    "Filipines": "Philippines",

    # Plot Puerto Rico separately. Change this to "United States"
    # if you prefer to fold Puerto Rico into the US count.
    "Puerto Rico (United States)": "Puerto Rico",
}


def clean_country(value):
    """Standardize country/nationality labels before mapping."""
    if pd.isna(value):
        return None

    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)

    if value.lower() in UNKNOWN_VALUES:
        return None

    return COUNTRY_FIXES.get(value, value)


def country_to_iso3(country):
    """Convert country names to ISO-3 codes for safer Plotly mapping."""
    code = coco.convert(names=country, to="ISO3", not_found=None)

    if code is None or code == "not found":
        return None

    return code


def make_choropleth(df, column, title, output_html, output_csv):
    counts = (
        df[column]
        .map(clean_country)
        .dropna()
        .value_counts()
        .rename_axis("Country")
        .reset_index(name="Participants")
    )

    counts["ISO3"] = counts["Country"].apply(country_to_iso3)

    unmatched = counts[counts["ISO3"].isna()]
    if not unmatched.empty:
        print(f"\nCountries not matched for {column}:")
        print(unmatched[["Country", "Participants"]])

    counts = counts.dropna(subset=["ISO3"])

    def count_group(n):
        if n == 1:
            return "1"
        elif n == 2:
            return "2"
        elif n == 3:
            return "3"
        elif 4 <= n <= 5:
            return "4–5"
        else:
            return "6+"

    counts["Count group"] = counts["Participants"].apply(count_group)

    category_order = ["1", "2", "3", "4–5", "6+"]

    color_map = {
        "1": "#fdd49e",
        "2": "#fdbb84",
        "3": "#fc8d59",
        "4–5": "#e34a33",
        "6+": "#b30000",
    }

    fig = px.choropleth(
        counts,
        locations="ISO3",
        color="Count group",
        hover_name="Country",
        hover_data={
            "ISO3": False,
            "Participants": True,
            "Count group": False,
        },
        category_orders={"Count group": category_order},
        color_discrete_map=color_map,
        projection="natural earth",
        title=title,
    )

    fig.add_trace(
        go.Scattergeo(
            lon=[12.3155],
            lat=[45.4408],
            mode="markers+text",
            marker=dict(
                size=15,
                color="black",
                line=dict(width=1, color="white"),
            ),
            text=["Venice"],
            textposition="middle right",
            textfont=dict(
                size=18,
                color="black",
            ),
            name="Course location",
            hovertemplate="<b>Venice, Italy</b><extra></extra>",
        )
    )

    fig.update_geos(
        showframe=False,
        showcoastlines=True,
        projection_type="natural earth",
    )

    fig.update_layout(
        coloraxis_colorbar_title="Participants",
        margin={"r": 0, "t": 60, "l": 0, "b": 0},
    )

    fig.write_html(output_html)
    counts.to_csv(output_csv, index=False)

    return counts


def main():
    df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME)

    affiliation_counts = make_choropleth(
        df,
        AFFILIATION_COL,
        "Participants by country of affiliation",
        "map_country_of_affiliation.html",
        "counts_country_of_affiliation.csv",
    )

    nationality_counts = make_choropleth(
        df,
        NATIONALITY_COL,
        "Participants by nationality",
        "map_nationality.html",
        "counts_nationality.csv",
    )

    print("\nCountry of affiliation counts:")
    print(affiliation_counts)

    print("\nNationality counts:")
    print(nationality_counts)

    print("\nDone. Open these files in your browser:")
    print("- map_country_of_affiliation.html")
    print("- map_nationality.html")


if __name__ == "__main__":
    main()