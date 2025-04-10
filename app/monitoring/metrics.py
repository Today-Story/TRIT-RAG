from prometheus_client import Counter

recommendation_failures_total = Counter(
    "recommendation_failures_total",
    "Total number of failed recommendations"
)
