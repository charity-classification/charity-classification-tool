from airtable import Airtable
import pandas as pd
from slugify import slugify

import settings


df = pd.read_pickle(settings.COMPLETED_DF)
corpus = pd.DataFrame([df["name"], df["activities"].fillna(df["objects"])]).T.apply(
    lambda x: " ".join(x), axis=1
)
tags_used = (
    df["Tags"]
    .apply(pd.Series)
    .unstack()
    .dropna()
    .value_counts()
    .rename("frequency")
    .to_frame()
    .reset_index()
    .rename(columns={"index": "tag"})
)
tags_used.loc[:, "tag_slug"] = tags_used["tag"].apply(slugify)

RESULT_TYPES = {
    "false-positive": "Records that should not have been selected but were",
    "false-negative": "Records that weren't selected but should have been",
    "true-positive": "Records that were correctly selected",
    "true-negative": "Records that were correctly not selected",
}


def get_tags_used():
    airtable = Airtable(
        settings.AIRTABLE_BASE_ID,
        settings.AIRTABLE_TAGS_TABLE_NAME,
        settings.AIRTABLE_API_KEY,
    )
    data = airtable.get_all()
    data = pd.DataFrame(
        index=[i["id"] for i in data],
        data=[i["fields"] for i in data],
    ).rename(columns={"Name": "tag"})
    data.loc[:, "tag_slug"] = data["tag"].apply(slugify)

    tags_used = (
        df["Tags"]
        .apply(pd.Series)
        .unstack()
        .dropna()
        .value_counts()
        .rename("frequency")
    )
    data = data.join(tags_used, on="tag")

    return data.sort_values("frequency", ascending=False)


def get_keyword_result(tag, keyword_regex):
    selected_items = corpus.str.contains(keyword_regex, regex=True, case=False)
    relevant_items = df["Tags"].apply(lambda x: tag in x if x else False)
    result = pd.DataFrame(
        {
            "selected": selected_items,
            "relevant": relevant_items,
        }
    )
    result.loc[result["selected"] & result["relevant"], "result"] = "true-positive"
    result.loc[result["selected"] & ~result["relevant"], "result"] = "false-positive"
    result.loc[~result["selected"] & ~result["relevant"], "result"] = "true-negative"
    result.loc[~result["selected"] & result["relevant"], "result"] = "false-negative"
    return result


def get_result_summary(result):
    result_summary = {
        "relevant": result["relevant"].sum(),
        "selected": result["selected"].sum(),
    }
    for r in RESULT_TYPES.keys():
        result_summary[r] = (result["result"] == r).sum()
    result_summary["precision"] = result_summary["true-positive"] / (
        result_summary["true-positive"] + result_summary["false-positive"]
    )
    result_summary["recall"] = result_summary["true-positive"] / (
        result_summary["true-positive"] + result_summary["false-negative"]
    )
    result_summary["f1score"] = 2 * (
        (result_summary["precision"] * result_summary["recall"])
        / (result_summary["precision"] + result_summary["recall"])
    )
    result_summary["accuracy"] = (
        result_summary["true-positive"] + result_summary["true-negative"]
    ) / len(result)
    return result_summary
