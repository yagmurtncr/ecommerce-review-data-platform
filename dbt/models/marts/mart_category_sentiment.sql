-- Sentiment & rating rolled up per category.
select
    category_name,
    count(*)                                         as reviews,
    round(avg(rating)::numeric, 3)                   as avg_rating,
    round(avg(sentiment_stars)::numeric, 3)          as avg_sentiment,
    sum(case when sentiment_label = 'positive' then 1 else 0 end) as positive_reviews,
    sum(case when sentiment_label = 'negative' then 1 else 0 end) as negative_reviews,
    sum(case when is_suspicious then 1 else 0 end)    as suspicious_reviews
from {{ ref('stg_reviews') }}
group by category_name
order by reviews desc
