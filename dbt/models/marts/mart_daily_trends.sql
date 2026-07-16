-- Daily review volume and rolling 7-day average rating (satisfaction trend).
with daily as (
    select
        review_date,
        count(*)                        as reviews,
        round(avg(rating)::numeric, 3)  as avg_rating
    from {{ ref('stg_reviews') }}
    group by review_date
)
select
    review_date,
    reviews,
    avg_rating,
    round(avg(avg_rating) over (
        order by review_date rows between 6 preceding and current row
    )::numeric, 3) as avg_rating_7d
from daily
order by review_date
