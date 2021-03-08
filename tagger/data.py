import warnings
from airtable import Airtable
import pandas as pd
from slugify import slugify

from tagger import settings
warnings.filterwarnings("ignore", 'This pattern has match groups')


RESULT_TYPES = {
    "false-positive": "Records that should not have been selected but were",
    "false-negative": "Records that weren't selected but should have been",
    "true-positive": "Records that were correctly selected",
    "true-negative": "Records that were correctly not selected",
}

def get_completed_data():
    df = pd.read_pickle(settings.COMPLETED_DF)
    corpus = pd.DataFrame([df["name"], df["activities"].fillna(df["objects"])]).T.apply(
        lambda x: " ".join(x), axis=1
    )
    return (df, corpus)


def save_tags_used(df):
    df.to_pickle(settings.TAGS_USED_DF)


def get_tags_used():
    return pd.read_pickle(settings.TAGS_USED_DF)


def initialise_data():
    df, corpus = get_completed_data()

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
    data = data[data["Not used (describe why)"].isnull()]
    data.loc[:, "tag_slug"] = data["tag"].apply(slugify)
    data.loc[:, "precision"] = pd.NA
    data.loc[:, "recall"] = pd.NA
    data.loc[:, "f1score"] = pd.NA
    data.loc[:, "accuracy"] = pd.NA

    tags_used = (
        df["Tags"]
        .apply(pd.Series)
        .unstack()
        .dropna()
        .value_counts()
        .rename("frequency")
    )
    data = data.join(tags_used, on="tag")

    for index, row in data[data["Regular expression"].notnull()].iterrows():
        result = get_keyword_result(row["tag"], row["Regular expression"], df, corpus)
        summary = get_result_summary(result)
        data.loc[index, "precision"] = summary["precision"]
        data.loc[index, "recall"] = summary["recall"]
        data.loc[index, "f1score"] = summary["f1score"]
        data.loc[index, "accuracy"] = summary["accuracy"]

    data = data.sort_values("frequency", ascending=False)
    save_tags_used(data)


def get_keyword_result(tag, keyword_regex, df, corpus):
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


def save_regex_to_airtable(tag_id, new_regex):
    if not new_regex or new_regex == settings.DEFAULT_REGEX:
        return False
    airtable = Airtable(
        settings.AIRTABLE_BASE_ID,
        settings.AIRTABLE_TAGS_TABLE_NAME,
        settings.AIRTABLE_API_KEY,
    )
    record = airtable.update(
        tag_id,
        {
            "Regular expression": new_regex,
        }
    )
    return True
