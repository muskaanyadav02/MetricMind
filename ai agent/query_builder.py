from schema import METRICS, DIMENSIONS


def identify_metric(question):
    question = question.lower()

    for metric in METRICS:
        if metric.lower() in question:
            return metric

    return None


def identify_dimension(question):
    question = question.lower()

    for dimension in DIMENSIONS:
        if dimension.lower() in question:
            return dimension

    return None


def build_query(question):
    return {
        "question": question,
        "metric": identify_metric(question),
        "dimension": identify_dimension(question)
    }