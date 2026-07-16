-- Wide, analysis-friendly view of the fact joined to its dimensions.
with f as (
    select * from {{ source('warehouse', 'fact_reviews') }}
)
select
    f.review_id,
    f.product_id,
    p.product_name,
    c.category_name,
    f.customer_id,
    d.full_date        as review_date,
    d.year             as review_year,
    d.month            as review_month,
    d.is_weekend,
    f.rating,
    f.sentiment_stars,
    f.sentiment_label,
    f.review_length,
    f.word_count,
    f.is_suspicious
from f
left join {{ source('warehouse', 'dim_product') }}  p on p.product_id  = f.product_id
left join {{ source('warehouse', 'dim_category') }}  c on c.category_id = f.category_id
left join {{ source('warehouse', 'dim_date') }}      d on d.date_id     = f.date_id
