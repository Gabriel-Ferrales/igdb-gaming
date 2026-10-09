select
    * except (id),
    id as company_id
from {{ source('gaming_raw', 'companies') }}
